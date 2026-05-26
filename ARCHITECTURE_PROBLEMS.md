# Architecture-Level Problems

## Problem 1: Entire Application in One File
`app/api/data.py` is 9,566 lines long and contains 73 API endpoints.  
All major features and business logic are bundled into a single file, making the system tightly coupled, difficult to test, risky to modify, and hard to scale or maintain.

## Problem 2: One Service Class Handles Everything
`app/services/supabase_service.py` contains a massive `SupabaseService` class with ~80 methods across multiple domains.  
The class violates single responsibility principles and acts as the entire data layer, causing maintainability and scalability issues.

## Problem 3: Route Handlers Calling Other Route Handlers
API route handlers directly call another route function (`get_reporting_dashboard`) instead of using shared service-layer logic.  
This breaks separation of concerns and mixes business logic into the routing layer.

## Problem 4: Multiple Competing Database Access Patterns
The application simultaneously uses:
- SQLAlchemy ORM
- SQLAlchemy Core with runtime table reflection
- Deprecated Supabase REST API

This unfinished migration creates inconsistency, technical debt, and noisy deprecation warnings in logs.

## Problem 5: Table Reflection Happens on Every Request
Database schema reflection is cached only per service instance, but service instances are recreated for every request.  
As a result, the application repeatedly reflects database schemas unnecessarily, causing avoidable performance overhead.

## Problem 6: Unfinished Brand vs Client Data Model
The application originally used a `Brand` model and later introduced a separate `Client` model without fully integrating them.  
This created overlapping responsibilities, inconsistent architecture, and unclear domain ownership across the system.