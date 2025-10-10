from typing import cast
from uuid import UUID
import pytest
from litestar.testing import TestClient
from main import app, pcs, employees, departments


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear the in-memory storage before each test."""
    pcs.clear()
    employees.clear()
    departments.clear()
    yield
    pcs.clear()
    employees.clear()
    departments.clear()


def test_create_pc():
    """Test POST /pcs - Create a new PC."""
    with TestClient(app=app) as client:
        pc_data = {
            "name": "Test PC",
            "model": "Dell XPS 15",
            "serial_number": "SN12345",
            "assigned_to": None,
        }
        response = client.post("/pcs", json=pc_data)

        assert response.status_code == 201
        data = cast(dict[str, str | None], response.json())
        assert data["name"] == "Test PC"
        assert data["model"] == "Dell XPS 15"
        assert data["serial_number"] == "SN12345"
        assert data["assigned_to"] is None
        assert "id" in data
        # Verify it's a valid UUID
        _ = UUID(data["id"])


def test_list_pcs_empty():
    """Test GET /pcs - List all PCs when empty."""
    with TestClient(app=app) as client:
        response = client.get("/pcs")

        assert response.status_code == 200
        assert response.json() == []


def test_list_pcs_with_data():
    """Test GET /pcs - List all PCs with data."""
    with TestClient(app=app) as client:
        # Create two PCs
        pc1_data = {
            "name": "PC 1",
            "model": "Model 1",
            "serial_number": "SN001",
            "assigned_to": None,
        }
        pc2_data = {
            "name": "PC 2",
            "model": "Model 2",
            "serial_number": "SN002",
            "assigned_to": None,
        }
        _ = client.post("/pcs", json=pc1_data)
        _ = client.post("/pcs", json=pc2_data)

        # List all PCs
        response = client.get("/pcs")

        assert response.status_code == 200
        data = cast(list[dict[str, str | None]], response.json())
        assert len(data) == 2
        assert data[0]["name"] == "PC 1"
        assert data[1]["name"] == "PC 2"


def test_get_pc():
    """Test GET /pcs/{pc_id} - Get a specific PC."""
    with TestClient(app=app) as client:
        # Create a PC
        pc_data = {
            "name": "Test PC",
            "model": "Dell XPS 15",
            "serial_number": "SN12345",
            "assigned_to": None,
        }
        create_response = client.post("/pcs", json=pc_data)
        pc_id = cast(str, create_response.json()["id"])

        # Get the PC
        response = client.get(f"/pcs/{pc_id}")

        assert response.status_code == 200
        data = cast(dict[str, str | None], response.json())
        assert data["id"] == pc_id
        assert data["name"] == "Test PC"
        assert data["model"] == "Dell XPS 15"


def test_get_pc_not_found():
    """Test GET /pcs/{pc_id} - PC not found."""
    with TestClient(app=app) as client:
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/pcs/{fake_id}")

        assert response.status_code == 404


def test_update_pc():
    """Test PUT /pcs/{pc_id} - Update a PC."""
    with TestClient(app=app) as client:
        # Create a department and employee first
        dept_response = client.post("/departments", json={"name": "IT"})
        dept_id = cast(str, dept_response.json()["id"])

        employee_data = {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "department_id": dept_id,
        }
        employee_response = client.post("/employees", json=employee_data)
        employee_id = cast(str, employee_response.json()["id"])

        # Create a PC
        pc_data = {
            "name": "Test PC",
            "model": "Dell XPS 15",
            "serial_number": "SN12345",
            "assigned_to": None,
        }
        create_response = client.post("/pcs", json=pc_data)
        pc_id = cast(str, create_response.json()["id"])

        # Update the PC
        updated_data = {
            "name": "Updated PC",
            "model": "Dell XPS 17",
            "serial_number": "SN99999",
            "assigned_to": employee_id,
        }
        response = client.put(f"/pcs/{pc_id}", json=updated_data)

        assert response.status_code == 200
        data = cast(dict[str, str | None], response.json())
        assert data["id"] == pc_id
        assert data["name"] == "Updated PC"
        assert data["model"] == "Dell XPS 17"
        assert data["serial_number"] == "SN99999"
        assert data["assigned_to"] == employee_id


def test_update_pc_not_found():
    """Test PUT /pcs/{pc_id} - PC not found."""
    with TestClient(app=app) as client:
        fake_id = "00000000-0000-0000-0000-000000000000"
        updated_data = {
            "name": "Updated PC",
            "model": "Dell XPS 17",
            "serial_number": "SN99999",
            "assigned_to": None,
        }
        response = client.put(f"/pcs/{fake_id}", json=updated_data)

        assert response.status_code == 404


def test_delete_pc():
    """Test DELETE /pcs/{pc_id} - Delete a PC."""
    with TestClient(app=app) as client:
        # Create a PC
        pc_data = {
            "name": "Test PC",
            "model": "Dell XPS 15",
            "serial_number": "SN12345",
            "assigned_to": None,
        }
        create_response = client.post("/pcs", json=pc_data)
        pc_id = cast(str, create_response.json()["id"])

        # Delete the PC
        response = client.delete(f"/pcs/{pc_id}")

        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/pcs/{pc_id}")
        assert get_response.status_code == 404


def test_delete_pc_not_found():
    """Test DELETE /pcs/{pc_id} - PC not found."""
    with TestClient(app=app) as client:
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/pcs/{fake_id}")

        assert response.status_code == 404


def test_crud_workflow():
    """Test complete CRUD workflow."""
    with TestClient(app=app) as client:
        # Create
        pc_data = {
            "name": "Workflow PC",
            "model": "HP Laptop",
            "serial_number": "SN-WORKFLOW",
            "assigned_to": None,
        }
        create_response = client.post("/pcs", json=pc_data)
        assert create_response.status_code == 201
        pc_id = cast(str, create_response.json()["id"])

        # Read (single)
        get_response = client.get(f"/pcs/{pc_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Workflow PC"

        # Read (list)
        list_response = client.get("/pcs")
        assert list_response.status_code == 200
        list_data = cast(list[dict[str, str | None]], list_response.json())
        assert len(list_data) == 1

        # Update
        updated_data = {
            "name": "Updated Workflow PC",
            "model": "HP EliteBook",
            "serial_number": "SN-WORKFLOW-2",
            "assigned_to": None,
        }
        update_response = client.put(f"/pcs/{pc_id}", json=updated_data)
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Workflow PC"

        # Delete
        delete_response = client.delete(f"/pcs/{pc_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        final_list = client.get("/pcs")
        final_data = cast(list[dict[str, str | None]], final_list.json())
        assert len(final_data) == 0


# Employee tests
def test_create_employee():
    """Test POST /employees - Create a new employee."""
    with TestClient(app=app) as client:
        # Create a department first
        department_data = {"name": "Engineering"}
        dept_response = client.post("/departments", json=department_data)
        department_id = cast(str, dept_response.json()["id"])

        employee_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "department_id": department_id,
        }
        response = client.post("/employees", json=employee_data)

        assert response.status_code == 201
        data = cast(dict[str, str | None], response.json())
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert data["department_id"] == department_id
        assert "id" in data
        _ = UUID(cast(str, data["id"]))


def test_list_employees():
    """Test GET /employees - List all employees."""
    with TestClient(app=app) as client:
        # Create departments first
        dept1_response = client.post("/departments", json={"name": "IT"})
        dept1_id = cast(str, dept1_response.json()["id"])
        dept2_response = client.post("/departments", json={"name": "HR"})
        dept2_id = cast(str, dept2_response.json()["id"])

        # Create employees
        employee1_data = {
            "name": "Employee 1",
            "email": "emp1@example.com",
            "department_id": dept1_id,
        }
        employee2_data = {
            "name": "Employee 2",
            "email": "emp2@example.com",
            "department_id": dept2_id,
        }
        _ = client.post("/employees", json=employee1_data)
        _ = client.post("/employees", json=employee2_data)

        response = client.get("/employees")

        assert response.status_code == 200
        data = cast(list[dict[str, str | None]], response.json())
        assert len(data) == 2


def test_pc_with_employee_assignment():
    """Test PC creation and update with employee assignment."""
    with TestClient(app=app) as client:
        # Create a department and employee
        dept_response = client.post("/departments", json={"name": "Engineering"})
        dept_id = cast(str, dept_response.json()["id"])

        employee_data = {
            "name": "Alice Smith",
            "email": "alice@example.com",
            "department_id": dept_id,
        }
        emp_response = client.post("/employees", json=employee_data)
        employee_id = cast(str, emp_response.json()["id"])

        # Create a PC assigned to the employee
        pc_data = {
            "name": "Alice's Laptop",
            "model": "MacBook Pro",
            "serial_number": "SN-ALICE-001",
            "assigned_to": employee_id,
        }
        pc_response = client.post("/pcs", json=pc_data)

        assert pc_response.status_code == 201
        pc_data_result = cast(dict[str, str | None], pc_response.json())
        assert pc_data_result["assigned_to"] == employee_id

        # Get the PC and verify assignment
        pc_id = pc_data_result["id"]
        get_response = client.get(f"/pcs/{pc_id}")
        assert get_response.status_code == 200
        assert get_response.json()["assigned_to"] == employee_id


def test_get_employee():
    """Test GET /employees/{employee_id} - Get a specific employee."""
    with TestClient(app=app) as client:
        # Create a department first
        dept_response = client.post("/departments", json={"name": "Sales"})
        dept_id = cast(str, dept_response.json()["id"])

        # Create an employee
        employee_data = {
            "name": "Bob Johnson",
            "email": "bob@example.com",
            "department_id": dept_id,
        }
        create_response = client.post("/employees", json=employee_data)
        employee_id = cast(str, create_response.json()["id"])

        # Get the employee
        response = client.get(f"/employees/{employee_id}")

        assert response.status_code == 200
        data = cast(dict[str, str | None], response.json())
        assert data["id"] == employee_id
        assert data["name"] == "Bob Johnson"
        assert data["email"] == "bob@example.com"
        assert data["department_id"] == dept_id


def test_get_employee_not_found():
    """Test GET /employees/{employee_id} - Employee not found."""
    with TestClient(app=app) as client:
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/employees/{fake_id}")

        assert response.status_code == 404


def test_update_employee():
    """Test PUT /employees/{employee_id} - Update an employee."""
    with TestClient(app=app) as client:
        # Create departments
        dept1_response = client.post("/departments", json={"name": "Marketing"})
        dept1_id = cast(str, dept1_response.json()["id"])
        dept2_response = client.post("/departments", json={"name": "Sales"})
        dept2_id = cast(str, dept2_response.json()["id"])

        # Create an employee
        employee_data = {
            "name": "Charlie Brown",
            "email": "charlie@example.com",
            "department_id": dept1_id,
        }
        create_response = client.post("/employees", json=employee_data)
        employee_id = cast(str, create_response.json()["id"])

        # Update the employee
        updated_data = {
            "name": "Charlie B. Brown",
            "email": "charlie.brown@example.com",
            "department_id": dept2_id,
        }
        response = client.put(f"/employees/{employee_id}", json=updated_data)

        assert response.status_code == 200
        data = cast(dict[str, str | None], response.json())
        assert data["id"] == employee_id
        assert data["name"] == "Charlie B. Brown"
        assert data["email"] == "charlie.brown@example.com"
        assert data["department_id"] == dept2_id


def test_update_employee_not_found():
    """Test PUT /employees/{employee_id} - Employee not found."""
    with TestClient(app=app) as client:
        # Create a department
        dept_response = client.post("/departments", json={"name": "IT"})
        dept_id = cast(str, dept_response.json()["id"])

        fake_id = "00000000-0000-0000-0000-000000000000"
        updated_data = {
            "name": "Test User",
            "email": "test@example.com",
            "department_id": dept_id,
        }
        response = client.put(f"/employees/{fake_id}", json=updated_data)

        assert response.status_code == 404


def test_delete_employee():
    """Test DELETE /employees/{employee_id} - Delete an employee."""
    with TestClient(app=app) as client:
        # Create a department first
        dept_response = client.post("/departments", json={"name": "Finance"})
        dept_id = cast(str, dept_response.json()["id"])

        # Create an employee
        employee_data = {
            "name": "David Miller",
            "email": "david@example.com",
            "department_id": dept_id,
        }
        create_response = client.post("/employees", json=employee_data)
        employee_id = cast(str, create_response.json()["id"])

        # Delete the employee
        response = client.delete(f"/employees/{employee_id}")

        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/employees/{employee_id}")
        assert get_response.status_code == 404


def test_delete_employee_not_found():
    """Test DELETE /employees/{employee_id} - Employee not found."""
    with TestClient(app=app) as client:
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/employees/{fake_id}")

        assert response.status_code == 404
