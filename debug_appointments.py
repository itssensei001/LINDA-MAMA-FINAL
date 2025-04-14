from app import app, db, User, DoctorProfile, MotherProfile, Appointment
from datetime import datetime
import os
from sqlalchemy import inspect

# Run this script to directly test appointment creation without going through API

def debug_appointment_creation():
    print("\n" + "="*80)
    print("APPOINTMENT DATABASE DEBUGGING")
    print("="*80)
    
    # First check database connection
    try:
        with app.app_context():
            print("Database connection: OK")
            
            # Check database tables - use SQLAlchemy inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables in database: {tables}")
            
            # Check if appointments table exists
            if 'appointments' not in tables:
                print("ERROR: appointments table does not exist in database!")
                return
            
            # Check model fields
            print("\nAppointment model fields:")
            for column in Appointment.__table__.columns:
                print(f"  - {column.name}: {column.type} (nullable={column.nullable})")
                for fk in column.foreign_keys:
                    print(f"    FK: {fk.target_fullname}")
            
            # Check users
            users = User.query.all()
            print(f"\nUsers in database: {len(users)}")
            for user in users:
                print(f"  - ID: {user.id}, Name: {user.full_name}, Role: {user.role}")
            
            # Check mother profiles
            mothers = MotherProfile.query.all()
            print(f"\nMother profiles in database: {len(mothers)}")
            for mother in mothers:
                user = User.query.get(mother.user_id)
                print(f"  - ID: {mother.id}, User ID: {mother.user_id}, Name: {user.full_name if user else 'Unknown'}")
            
            # Check doctor profiles
            doctors = DoctorProfile.query.all()
            print(f"\nDoctor profiles in database: {len(doctors)}")
            for doctor in doctors:
                user = User.query.get(doctor.user_id)
                print(f"  - ID: {doctor.id}, User ID: {doctor.user_id}, Name: {user.full_name if user else 'Unknown'}")
            
            # Check existing appointments
            appointments = Appointment.query.all()
            print(f"\nAppointments in database: {len(appointments)}")
            for appt in appointments:
                mother_user = User.query.get(appt.mother_id)
                doctor_user = User.query.get(appt.doctor_id)
                print(f"  - ID: {appt.id}, Mother: {mother_user.full_name if mother_user else 'Unknown'}, Doctor: {doctor_user.full_name if doctor_user else 'Unknown'}, Date: {appt.date}")
            
            # Try to create an appointment directly
            print("\nAttempting to create test appointment...")
            
            # Get first doctor and mother
            if not doctors:
                print("ERROR: No doctors in database!")
                return
                
            if not mothers:
                print("ERROR: No mothers in database!")
                return
                
            test_doctor = doctors[0]
            test_mother = mothers[0]
            
            print(f"Using doctor ID: {test_doctor.id}, user_id: {test_doctor.user_id}")
            print(f"Using mother ID: {test_mother.id}, user_id: {test_mother.user_id}")
            
            # Create appointment
            try:
                print("DIRECT METHOD - Using doctor's profile.id")
                appt1 = Appointment(
                    mother_id=test_mother.user_id,  # mother's user_id
                    doctor_id=test_doctor.id,       # doctor's profile.id
                    date=datetime.now().date(),
                    time=datetime.now().time(),
                    appointment_type="Test Appointment",
                    status='scheduled'
                )
                
                db.session.add(appt1)
                db.session.flush()  # Test but don't commit
                print(f"Test 1 success - Appointment: {appt1.id}, Mother: {appt1.mother_id}, Doctor: {appt1.doctor_id}")
                db.session.rollback()  # Don't actually save it
                
                # Try alternate method
                print("\nALTERNATE METHOD - Using doctor's user_id")
                appt2 = Appointment(
                    mother_id=test_mother.user_id,  # mother's user_id
                    doctor_id=test_doctor.user_id,  # doctor's user_id
                    date=datetime.now().date(),
                    time=datetime.now().time(),
                    appointment_type="Test Appointment 2",
                    status='scheduled'
                )
                
                db.session.add(appt2)
                db.session.flush()  # Test but don't commit
                print(f"Test 2 success - Appointment: {appt2.id}, Mother: {appt2.mother_id}, Doctor: {appt2.doctor_id}")
                db.session.rollback()  # Don't actually save it
                
                print("\nCONFIRMED WORKING METHOD:")
                if 'doctor_profiles.user_id' in str(Appointment.__table__.columns['doctor_id'].foreign_keys):
                    print("Doctor ID should be doctor_profile.user_id")
                    doctor_id_to_use = test_doctor.user_id
                elif 'doctor_profiles.id' in str(Appointment.__table__.columns['doctor_id'].foreign_keys):
                    print("Doctor ID should be doctor_profile.id")
                    doctor_id_to_use = test_doctor.id
                else:
                    print("Uncertain what doctor_id should be - check table definition")
                    return
                
                # Final test with commit
                print("\nFINAL TEST WITH COMMIT")
                appt3 = Appointment(
                    mother_id=test_mother.user_id,
                    doctor_id=doctor_id_to_use,
                    date=datetime.now().date(),
                    time=datetime.now().time(),
                    appointment_type="Debug Test Appointment",
                    status='scheduled'
                )
                
                db.session.add(appt3)
                db.session.commit()
                print(f"Success - created appointment ID: {appt3.id}")
                
                # Verify it exists
                saved = Appointment.query.get(appt3.id)
                if saved:
                    print(f"Verified appointment in database: ID={saved.id}, mother={saved.mother_id}, doctor={saved.doctor_id}")
                else:
                    print("ERROR: Could not find appointment after commit!")
                
            except Exception as e:
                db.session.rollback()
                print(f"ERROR: Failed to create appointment: {e}")
                import traceback
                traceback.print_exc()
                
                # Check for foreign key constraint violations
                error_msg = str(e).lower()
                if "foreign key constraint" in error_msg:
                    if "doctor_id" in error_msg:
                        print("\nFOREIGN KEY ISSUE WITH DOCTOR_ID:")
                        print(f"- doctor_id being used: {test_doctor.id}")
                        print("- Checking if this ID exists in the referenced table...")
                        
                        if 'doctor_profiles.user_id' in str(Appointment.__table__.columns['doctor_id'].foreign_keys):
                            target_docs = User.query.filter_by(id=test_doctor.id).all()
                            print(f"  Doctor ID should reference users table: {[d.id for d in target_docs]}")
                        else:
                            target_docs = DoctorProfile.query.filter_by(id=test_doctor.id).all()
                            print(f"  Doctor ID should reference doctor_profiles table: {[d.id for d in target_docs]}")
                        
                    if "mother_id" in error_msg:
                        print("\nFOREIGN KEY ISSUE WITH MOTHER_ID:")
                        print(f"- mother_id being used: {test_mother.user_id}")
                        print("- Checking if this ID exists in mother_profiles.user_id...")
                        target_moms = MotherProfile.query.filter_by(user_id=test_mother.user_id).all()
                        print(f"  Found: {[m.user_id for m in target_moms]}")
    
    except Exception as e:
        print(f"General error in debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_appointment_creation() 