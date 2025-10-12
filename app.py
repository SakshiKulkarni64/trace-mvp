import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import spacy
from datetime import datetime
import threading
import random

# =======================
# DATABASE SETUP
# =======================
DB_FILE = "trace_mvp.db"
engine = create_engine(f"sqlite:///{DB_FILE}")
Base = declarative_base()

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    contact = Column(String(50))
    area = Column(String(50))
    incident_date = Column(String(50))
    incident_place = Column(String(50))
    description = Column(Text)
    formatted_text = Column(Text)
    status = Column(String(50))
    officer_assigned = Column(String(50))
    station = Column(String(50))
    phone = Column(String(50))

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# =======================
# NLP SETUP
# =======================
nlp = spacy.load("en_core_web_sm")

def extract_entities(text):
    doc = nlp(text)
    persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    locations = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    return persons, locations

def format_complaint(name, contact, area, incident_date, incident_place, description):
    persons, locations = extract_entities(description)
    formatted = f"""
Formal Complaint Report
-----------------------
Complainant Name: {name}
Contact Number: {contact}
Residential Area: {area}

Incident Date: {incident_date}
Incident Place: {incident_place}

Complaint Description:
{description}

Identified Persons: {', '.join(persons) if persons else 'N/A'}
Possible Locations: {', '.join(locations) if locations else 'N/A'}

Date Filed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Signature: ______________________
"""
    return formatted

# =======================
# OFFICER POOL
# =======================
officers = [
    {"name": "SI Karishma Singh", "station": "Lal Bazaar Station", "phone": "9812345670"},
    {"name": "Head Constable Pushpa Singh", "station": "Indiranagar Station", "phone": "9823456781"},
    {"name": "SHO Haseena Malik", "station": "Connaught Place Station", "phone": "9834567892"},
    {"name": "SHO Bulbul Pandey", "station": "Bandra Station", "phone": "9845678903"},
    {"name": "Constable Santosh Sharma", "station": "MG Road Station", "phone": "9856789014"},
    {"name": "Constable Cheetah Chaturvedi", "station": "Rajajinagar Station", "phone": "9867890125"},
    {"name": "SI Srikanth Tiwari", "station": "Yeshwantpur Station", "phone": "9878901236"},
    {"name": "SI Naina Mathur", "station": "Jayanagar Station", "phone": "9889012347"},
]


def assign_officer(case_id):
    case = session.query(Complaint).filter_by(id=case_id).first()
    if case and case.officer_assigned == "Not Assigned":
        officer = random.choice(officers)
        case.officer_assigned = officer["name"]
        case.station = officer["station"]
        case.phone = officer["phone"]
        case.status = "Assigned"
        session.commit()

# =======================
# STREAMLIT UI
# =======================
st.set_page_config(page_title="TRACE - Crime Reporting", layout="wide")
st.sidebar.title("TRACE System")
menu = st.sidebar.radio("Select an option", ["Register Complaint", "Track Investigation", "Contact Officer", "Admin"])

# 1️⃣ REGISTER COMPLAINT
if menu == "Register Complaint":
    st.title("Register a Complaint")

    name = st.text_input("Your Name")
    contact = st.text_input("Contact Number")
    area = st.text_input("Residential Area")
    incident_date = st.date_input("Incident Date")
    incident_place = st.text_input("Incident Location")
    description = st.text_area("Describe the incident")

    if st.button("Submit Complaint"):
        if name and contact and area and incident_place and description:
            formatted_text = format_complaint(name, contact, area, str(incident_date), incident_place, description)
            new_complaint = Complaint(
                name=name,
                contact=contact,
                area=area,
                incident_date=str(incident_date),
                incident_place=incident_place,
                description=description,
                formatted_text=formatted_text,
                status="Under Review",
                officer_assigned="Not Assigned",
                station="N/A",
                phone="N/A"
            )
            session.add(new_complaint)
            session.commit()
            st.success("Complaint registered successfully.")
            st.info(f"Your case ID is: {new_complaint.id}")
            st.download_button("Download Formal Complaint", formatted_text)

            # Schedule officer assignment
            threading.Timer(15, assign_officer, args=[new_complaint.id]).start()
        else:
            st.warning("Please fill all fields before submitting.")

# 2️⃣ TRACK INVESTIGATION
elif menu == "Track Investigation":
    st.title("Track Your Investigation")
    contact = st.text_input("Enter your contact number to check status")
    if st.button("Track"):
        result = session.query(Complaint).filter_by(contact=contact).all()
        if result:
            for r in result:
                st.subheader(f"Case ID: {r.id}")
                st.write(f"Status: {r.status}")
                st.write(f"Officer Assigned: {r.officer_assigned}")
                st.write(f"Station: {r.station}")
                st.write(f"Phone: {r.phone}")
        else:
            st.warning("No complaint found with this contact number.")

# 3️⃣ CONTACT OFFICER
elif menu == "Contact Officer":
    st.title("Contact Officer Assigned to Your Case")
    case_id = st.number_input("Enter Case ID", min_value=1, step=1)
    if st.button("Find Officer"):
        r = session.query(Complaint).filter_by(id=case_id).first()
        if r:
            if r.officer_assigned != "Not Assigned":
                st.success(f"Officer Name: {r.officer_assigned}")
                st.info(f"Station: {r.station}")
                st.info(f"Phone: {r.phone}")
            else:
                st.warning("Officer not yet assigned for this case.")
        else:
            st.error("No case found with this ID.")

# 4️⃣ ADMIN VIEW
elif menu == "Admin":
    st.title("Admin Panel - Update Case Status")
    password = st.text_input("Enter Admin Password", type="password")
    if password == "secure123":  # 🔐 Replace with hashed check in production
        case_id = st.number_input("Enter Case ID to Update", min_value=1, step=1)
        new_status = st.text_input("New Status")
        officer = st.text_input("Officer Name")
        station = st.text_input("Police Station Area")
        phone = st.text_input("Officer Contact Number")

        if st.button("Update Case"):
            case = session.query(Complaint).filter_by(id=case_id).first()
            if case:
                case.status = new_status or case.status
                case.officer_assigned = officer or case.officer_assigned
                case.station = station or case.station
                case.phone = phone or case.phone
                session.commit()
                st.success("Case details updated successfully.")
            else:
                st.warning("No case found with this ID.")
    elif password:
        st.error("Incorrect password.")
