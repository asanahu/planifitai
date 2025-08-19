from fastapi.testclient import TestClient


def unwrap(j):
    return j.get("data", j)


def ensure_exercise(db, **kwargs):
    try:
        from tests.factories import exercise_factory

        return exercise_factory(**kwargs)
    except Exception:  # pragma: no cover - factories may not exist
        try:
            from app.routines.models import ExerciseCatalog as Exercise
        except Exception:  # pragma: no cover - fallback if location differs
            from app.exercises.models import Exercise  # type: ignore

        data = {"name": kwargs.get("name")}
        if "equipment" in kwargs:
            data["equipment"] = kwargs["equipment"]
        if "muscle_groups" in kwargs:
            mg = kwargs["muscle_groups"]
            if isinstance(mg, list):
                data["category"] = ",".join(mg)
            else:
                data["category"] = str(mg)
        if "level" in kwargs:
            data["description"] = kwargs["level"]

        ex = Exercise(**data)
        db.add(ex)
        db.commit()
        db.refresh(ex)
        return ex


def test_list_default_sorted_by_name(test_client: TestClient, db_session):
    ensure_exercise(
        db_session,
        name="push up",
        muscle_groups=["chest"],
        equipment="bodyweight",
        level="beginner",
    )
    ensure_exercise(
        db_session,
        name="Air Squat",
        muscle_groups=["legs"],
        equipment="bodyweight",
        level="beginner",
    )
    ensure_exercise(
        db_session,
        name="Dumbbell Row",
        muscle_groups=["back"],
        equipment="dumbbell",
        level="intermediate",
    )

    r = test_client.get("/api/v1/routines/exercise-catalog")
    assert r.status_code == 200, r.text
    data = unwrap(r.json())
    names = [it["name"] for it in data["items"]]
    assert names == sorted(names, key=str.lower)
    assert data["limit"] == 50 and data["offset"] == 0


def test_filter_by_q_and_muscle(test_client: TestClient, db_session):
    ensure_exercise(
        db_session,
        name="Push Up",
        muscle_groups=["chest"],
        equipment="bodyweight",
        level="beginner",
    )
    ensure_exercise(
        db_session,
        name="Pull Up",
        muscle_groups=["back"],
        equipment="bodyweight",
        level="intermediate",
    )

    r = test_client.get("/api/v1/routines/exercise-catalog?q=push&muscle=chest")
    assert r.status_code == 200
    data = unwrap(r.json())
    assert len(data["items"]) >= 1
    assert all("push" in it["name"].lower() for it in data["items"])


def test_filter_by_equipment_and_level(test_client: TestClient, db_session):
    ensure_exercise(
        db_session,
        name="Dumbbell Row",
        muscle_groups=["back"],
        equipment="dumbbell",
        level="intermediate",
    )
    ensure_exercise(
        db_session,
        name="Barbell Row",
        muscle_groups=["back"],
        equipment="barbell",
        level="intermediate",
    )

    r = test_client.get(
        "/api/v1/routines/exercise-catalog?equipment=dumbbell&level=intermediate"
    )
    assert r.status_code == 200
    data = unwrap(r.json())
    for it in data["items"]:
        assert (it.get("equipment") or "").lower() == "dumbbell"
        assert (it.get("level") or "").lower() == "intermediate"


def test_pagination_limit_offset(test_client: TestClient, db_session):
    ensure_exercise(
        db_session,
        name="Exercise A",
        muscle_groups=["legs"],
        equipment="bodyweight",
        level="beginner",
    )
    ensure_exercise(
        db_session,
        name="Exercise B",
        muscle_groups=["legs"],
        equipment="bodyweight",
        level="beginner",
    )
    ensure_exercise(
        db_session,
        name="Exercise C",
        muscle_groups=["legs"],
        equipment="bodyweight",
        level="beginner",
    )

    r = test_client.get("/api/v1/routines/exercise-catalog?limit=2&offset=1")
    assert r.status_code == 200
    data = unwrap(r.json())
    assert data["limit"] == 2 and data["offset"] == 1
    assert len(data["items"]) <= 2
    assert isinstance(data["total"], int)


def test_validation_bounds(test_client: TestClient):
    assert (
        test_client.get("/api/v1/routines/exercise-catalog?limit=0").status_code == 422
    )
    assert (
        test_client.get("/api/v1/routines/exercise-catalog?limit=101").status_code
        == 422
    )
    assert (
        test_client.get("/api/v1/routines/exercise-catalog?offset=-1").status_code
        == 422
    )
