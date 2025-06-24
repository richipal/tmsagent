"""
Script to set up sample data in BigQuery for testing the multi-agent system
"""

import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

def create_sample_tables():
    """Create sample tables with data for testing"""
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    dataset_id = os.getenv('BIGQUERY_DATASET_ID', 'data_science_agents')
    
    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT environment variable is required")
        return
    
    try:
        client = bigquery.Client(project=project_id)
        
        # Create dataset if it doesn't exist
        dataset_ref = client.dataset(dataset_id)
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        dataset.description = "Data Science Multi-Agent System Sample Dataset"
        
        try:
            client.create_dataset(dataset)
            print(f"Created dataset {dataset_id}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"Dataset {dataset_id} already exists")
            else:
                print(f"Error creating dataset: {e}")
                return
        
        # Create sample sales data table
        sales_table_id = f"{project_id}.{dataset_id}.sales_data"
        
        sales_schema = [
            bigquery.SchemaField("transaction_id", "STRING", mode="REQUIRED", description="Unique transaction identifier"),
            bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED", description="Customer identifier"),
            bigquery.SchemaField("product_id", "STRING", mode="REQUIRED", description="Product identifier"),
            bigquery.SchemaField("product_name", "STRING", mode="REQUIRED", description="Name of the product"),
            bigquery.SchemaField("category", "STRING", mode="REQUIRED", description="Product category"),
            bigquery.SchemaField("quantity", "INTEGER", mode="REQUIRED", description="Quantity purchased"),
            bigquery.SchemaField("unit_price", "FLOAT", mode="REQUIRED", description="Price per unit"),
            bigquery.SchemaField("total_amount", "FLOAT", mode="REQUIRED", description="Total transaction amount"),
            bigquery.SchemaField("transaction_date", "DATE", mode="REQUIRED", description="Date of transaction"),
            bigquery.SchemaField("sales_rep_id", "STRING", mode="NULLABLE", description="Sales representative ID"),
            bigquery.SchemaField("region", "STRING", mode="REQUIRED", description="Sales region"),
        ]
        
        # Create table
        sales_table = bigquery.Table(sales_table_id, schema=sales_schema)
        try:
            sales_table = client.create_table(sales_table)
            print(f"Created table {sales_table.table_id}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"Table {sales_table_id} already exists")
            else:
                print(f"Error creating sales table: {e}")
        
        # Insert sample data
        sample_sales_data = [
            {
                "transaction_id": "TXN001",
                "customer_id": "CUST001",
                "product_id": "PROD001",
                "product_name": "Laptop Pro 15",
                "category": "Electronics",
                "quantity": 1,
                "unit_price": 1299.99,
                "total_amount": 1299.99,
                "transaction_date": "2024-01-15",
                "sales_rep_id": "REP001",
                "region": "North America"
            },
            {
                "transaction_id": "TXN002",
                "customer_id": "CUST002",
                "product_id": "PROD002",
                "product_name": "Wireless Mouse",
                "category": "Electronics",
                "quantity": 2,
                "unit_price": 29.99,
                "total_amount": 59.98,
                "transaction_date": "2024-01-16",
                "sales_rep_id": "REP001",
                "region": "North America"
            },
            {
                "transaction_id": "TXN003",
                "customer_id": "CUST003",
                "product_id": "PROD003",
                "product_name": "Office Chair",
                "category": "Furniture",
                "quantity": 1,
                "unit_price": 199.99,
                "total_amount": 199.99,
                "transaction_date": "2024-01-17",
                "sales_rep_id": "REP002",
                "region": "Europe"
            },
            {
                "transaction_id": "TXN004",
                "customer_id": "CUST001",
                "product_id": "PROD004",
                "product_name": "Smartphone",
                "category": "Electronics",
                "quantity": 1,
                "unit_price": 899.99,
                "total_amount": 899.99,
                "transaction_date": "2024-01-18",
                "sales_rep_id": "REP003",
                "region": "Asia"
            },
            {
                "transaction_id": "TXN005",
                "customer_id": "CUST004",
                "product_id": "PROD005",
                "product_name": "Coffee Maker",
                "category": "Appliances",
                "quantity": 1,
                "unit_price": 89.99,
                "total_amount": 89.99,
                "transaction_date": "2024-01-19",
                "sales_rep_id": "REP002",
                "region": "Europe"
            }
        ]
        
        try:
            errors = client.insert_rows_json(sales_table, sample_sales_data)
            if errors:
                print(f"Error inserting data: {errors}")
            else:
                print(f"Inserted {len(sample_sales_data)} rows into sales_data table")
        except Exception as e:
            print(f"Error inserting sample data: {e}")
        
        # Create customers table
        customers_table_id = f"{project_id}.{dataset_id}.customers"
        
        customers_schema = [
            bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED", description="Customer identifier"),
            bigquery.SchemaField("customer_name", "STRING", mode="REQUIRED", description="Customer full name"),
            bigquery.SchemaField("email", "STRING", mode="REQUIRED", description="Customer email address"),
            bigquery.SchemaField("phone", "STRING", mode="NULLABLE", description="Customer phone number"),
            bigquery.SchemaField("address", "STRING", mode="NULLABLE", description="Customer address"),
            bigquery.SchemaField("city", "STRING", mode="NULLABLE", description="Customer city"),
            bigquery.SchemaField("state", "STRING", mode="NULLABLE", description="Customer state"),
            bigquery.SchemaField("country", "STRING", mode="REQUIRED", description="Customer country"),
            bigquery.SchemaField("registration_date", "DATE", mode="REQUIRED", description="Customer registration date"),
            bigquery.SchemaField("customer_segment", "STRING", mode="REQUIRED", description="Customer segment"),
        ]
        
        customers_table = bigquery.Table(customers_table_id, schema=customers_schema)
        try:
            customers_table = client.create_table(customers_table)
            print(f"Created table {customers_table.table_id}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"Table {customers_table_id} already exists")
            else:
                print(f"Error creating customers table: {e}")
        
        # Insert sample customer data
        sample_customers_data = [
            {
                "customer_id": "CUST001",
                "customer_name": "John Smith",
                "email": "john.smith@email.com",
                "phone": "+1-555-123-4567",
                "address": "123 Main St",
                "city": "New York",
                "state": "NY",
                "country": "USA",
                "registration_date": "2023-06-15",
                "customer_segment": "Premium"
            },
            {
                "customer_id": "CUST002",
                "customer_name": "Sarah Johnson",
                "email": "sarah.johnson@email.com",
                "phone": "+1-555-987-6543",
                "address": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "country": "USA",
                "registration_date": "2023-08-22",
                "customer_segment": "Standard"
            },
            {
                "customer_id": "CUST003",
                "customer_name": "Michel Dubois",
                "email": "michel.dubois@email.com",
                "phone": "+33-1-23-45-67-89",
                "address": "789 Rue de la Paix",
                "city": "Paris",
                "state": "Île-de-France",
                "country": "France",
                "registration_date": "2023-09-10",
                "customer_segment": "Premium"
            },
            {
                "customer_id": "CUST004",
                "customer_name": "Akira Tanaka",
                "email": "akira.tanaka@email.com",
                "phone": "+81-3-1234-5678",
                "address": "321 Shibuya Crossing",
                "city": "Tokyo",
                "state": "Tokyo",
                "country": "Japan",
                "registration_date": "2023-07-05",
                "customer_segment": "Premium"
            }
        ]
        
        try:
            errors = client.insert_rows_json(customers_table, sample_customers_data)
            if errors:
                print(f"Error inserting customer data: {errors}")
            else:
                print(f"Inserted {len(sample_customers_data)} rows into customers table")
        except Exception as e:
            print(f"Error inserting customer sample data: {e}")
        
        print(f"\n✅ Sample data setup complete!")
        print(f"Dataset: {project_id}.{dataset_id}")
        print(f"Tables created:")
        print(f"  - sales_data ({len(sample_sales_data)} rows)")
        print(f"  - customers ({len(sample_customers_data)} rows)")
        print(f"\nYou can now test the BigQuery agents with real data!")
        
    except Exception as e:
        print(f"Error setting up sample data: {e}")

if __name__ == "__main__":
    create_sample_tables()