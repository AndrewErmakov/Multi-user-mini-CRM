# Multi-user-mini-CRM

Architecture Description:

**Models** are required to represent the structure of data and business entities.
Their responsibilities include:

    1. Defining the structure of database tables using SQLAlchemy
    2. Data validation at the database level
    3. Relationships between entities
    4. Entity-level business logic

**Repositories** act as data access layers. Their responsibilities include:

    1. Abstraction over database operations
    2. CRUD operations (Create, Read, Update, Delete)
    3. Complex SQL queries
    4. Isolation of database logic from business logic

**Services** - the application's business logic.

Their responsibilities include:

    1. Business process orchestration
    2. Business rule validation
    3. Coordination between multiple repositories
    4. Transactional logic
    5. Data transformation between layers

**API-endpoints** need for application HTTP interface.

Their responsibilities:

    1. Processing HTTP requests and responses
    2. Input data validation via Pydantic schemas
    3. Authentication and authorization
    4. Converting exceptions to HTTP statuses
    5. Request routing

**Schemas** need for data validation and serialization.

**Dependencies** - FastAPI DI.

<hr>

Launch CRM

`docker-compose up -d`