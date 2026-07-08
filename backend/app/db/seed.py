import datetime
from sqlalchemy.orm import Session
try:
    from .session import engine, SessionLocal, Base
    from . import models
except ImportError:
    from session import engine, SessionLocal, Base
    import models

def seed_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

    db: Session = SessionLocal()
    try:
        # Check if tables are already seeded
        if db.query(models.User).first():
            print("Database already contains data. Skipping seeding.")
            return

        # Seed Users
        default_user = models.User(
            name="Vivek Nagare",
            email="vivek.nagare@lifeorg.com",
            role="field_rep"
        )
        db.add(default_user)
        db.flush() # get user id
        user_id = default_user.id
        print(f"Seeded User: {default_user.name} (ID: {user_id})")

        # Seed HCPs
        hcps = [
            models.HCP(
                name="Dr. Anil Sharma",
                specialty="Cardiology",
                hospital_affiliation="Metro Heart Institute",
                email="anil.sharma@metroheart.com",
                phone="+91 98765 43210",
                preferred_channel="visit",
                notes="Prefers morning visits between 9 AM and 11 AM. Interested in clinical trial data for CardioShield."
            ),
            models.HCP(
                name="Dr. Sunita Mehta",
                specialty="Endocrinology",
                hospital_affiliation="Max Super Speciality Hospital",
                email="sunita.mehta@maxhealth.com",
                phone="+91 98234 56789",
                preferred_channel="email",
                notes="Always ask for sample insulin pens. Prefers communication via email for product updates."
            ),
            models.HCP(
                name="Dr. Rajesh Patel",
                specialty="Oncology",
                hospital_affiliation="Tata Cancer Care Center",
                email="r.patel@tatacancer.org",
                phone="+91 91234 56789",
                preferred_channel="call",
                notes="Very busy. Keep calls brief and focused on drug efficacy and side effect profiles."
            ),
            models.HCP(
                name="Dr. Priya Nair",
                specialty="Pediatrics",
                hospital_affiliation="Fortis Children Clinic",
                email="priya.nair@fortis.com",
                phone="+91 90123 45678",
                preferred_channel="visit",
                notes="Interested in pediatric dosage guidelines for new vaccines. Likes colorful charts."
            ),
            models.HCP(
                name="Dr. Sanjay Gupta",
                specialty="General Medicine",
                hospital_affiliation="Apollo Clinic",
                email="sanjay.gupta@apollo.com",
                phone="+91 89012 34567",
                preferred_channel="call",
                notes="Friendly. Open to scheduling virtual webinars."
            )
        ]
        db.add_all(hcps)
        db.flush()
        print("Seeded 5 Healthcare Professionals.")

        # Seed Interactions
        sharma = hcps[0]
        mehta = hcps[1]
        
        interactions = [
            models.Interaction(
                hcp_id=sharma.id,
                user_id=user_id,
                interaction_type="visit",
                interaction_date=datetime.datetime.utcnow() - datetime.timedelta(days=5),
                channel="visit",
                topics_discussed=["CardioShield Launch", "Clinical Trial Phase III Results"],
                products_discussed=["CardioShield"],
                sentiment="positive",
                summary="Dr. Sharma was highly receptive to CardioShield. He appreciated the safety data and requested 10 sample packs to evaluate with selected patients.",
                raw_input="Visited Dr. Sharma at Metro Heart. Detailed CardioShield safety and efficacy data. He was happy and requested 10 samples.",
                source="form",
                follow_up_required=True,
                follow_up_date=(datetime.date.today() + datetime.timedelta(days=7)),
                samples_distributed={"CardioShield 10mg": 10}
            ),
            models.Interaction(
                hcp_id=mehta.id,
                user_id=user_id,
                interaction_type="email",
                interaction_date=datetime.datetime.utcnow() - datetime.timedelta(days=2),
                channel="email",
                topics_discussed=["Glynase Insulin Pens Update", "Dosage adjustments"],
                products_discussed=["Glynase"],
                sentiment="neutral",
                summary="Sent Glynase updates email. Dr. Mehta replied asking for physical samples of Glynase Pens on next physical visit.",
                raw_input="Emailed Dr. Sunita Mehta regarding Glynase updates. She replied asking for samples during the next visit.",
                source="chat",
                follow_up_required=True,
                follow_up_date=(datetime.date.today() + datetime.timedelta(days=14)),
                samples_distributed={}
            )
        ]
        db.add_all(interactions)
        db.commit()
        print("Seeded initial interactions.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
