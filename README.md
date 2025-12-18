# Online Job Marketing Application

Design and develop a full-stack online job marketplace where clients can post jobs, and freelancers can search, apply, communicate, and complete projects through a structured workflow.

## Project Highlights:
- Build a real-world job marketplace platform.
- Implement role-based access control for users.
- Employ Django's Model-View-Template (MVT) architecture.
- Integrate a MySQL relational database to ensure data integrity and relationships.
- Deliver a clean, user-friendly interface for seamless navigation.

---

## System Design

### Key Entities:
1. **User**
2. **Freelancer**
3. **Client**
4. **Skill**
5. **Job**
6. **Category**
7. **Application**
8. **Interview**
9. **Offer**
10. **Job Completion**
11. **Verification**

### Entity Relationships:
- **User** → **Freelancer** / **Client**: (1-to-1)
  - Each **User** profile is associated with either a **Freelancer** or a **Client**.

- **Freelancer** ⇄ **Skill**: (Many-to-Many)
  - Freelancers can have multiple skills, and each skill can belong to multiple freelancers.

- **Client** → **Job**: (1-to-Many)
  - A client can post multiple **Jobs**.

- **Job** → **Application**: (1-to-Many)
  - A **Job** can have multiple **Applications**.

- **Application** → **Interview**: (1-to-1)
  - Each **Application** may proceed to an **Interview** stage.

- **Application** → **Offer**: (1-to-1)
  - Each **Application** may receive one **Offer**.

- **Job** → **Job Completion**: (1-to-1)
  - A **Job** is associated with one **Job Completion** record once finalized.

---

## Technology Stack

### Backend:
- **Django (Python)**

### Database:
- **MySQL**

### Frontend:
- **HTML**
- **CSS**
- **Bootstrap**

### Template Engine:
- **Django Templates**

---