from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError

from app.core.logging import database_logger
from app.core.log_utils import log_database_operation

# Type variables for generic repository
T = TypeVar("T")  # Entity type
CreateSchemaType = TypeVar("CreateSchemaType")  # Create schema type
UpdateSchemaType = TypeVar("UpdateSchemaType")  # Update schema type


class IRepository(ABC, Generic[T, CreateSchemaType, UpdateSchemaType]):
    """
    Repository interface defining the contract for data access operations.

    This interface follows the Repository pattern, providing a consistent
    API for CRUD operations regardless of the underlying data store.
    """

    @abstractmethod
    def create(self, obj_in: CreateSchemaType) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get multiple entities with optional filtering."""
        pass

    @abstractmethod
    def update(self, id: int, obj_in: UpdateSchemaType) -> Optional[T]:
        """Update an existing entity."""
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete an entity by ID."""
        pass

    @abstractmethod
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filters."""
        pass


class BaseRepository(IRepository[T, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository implementation providing common CRUD operations.

    This abstract class implements the IRepository interface and provides
    common functionality that can be inherited by specific repositories.
    """

    def __init__(self, db: Session, model: type[T]):
        """
        Initialize the repository.

        Args:
            db: Database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model

    @log_database_operation("create")
    def create(self, obj_in: CreateSchemaType) -> T:
        """
        Create a new entity in the database.

        Args:
            obj_in: Pydantic schema with creation data

        Returns:
            Created entity instance

        Raises:
            IntegrityError: When database constraints are violated
        """
        try:
            # Convert pydantic model to dict
            obj_data = (
                obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in.dict()
            )

            # Create model instance
            db_obj = self.model(**obj_data)

            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)

            return db_obj

        except IntegrityError as e:
            self.db.rollback()
            database_logger.error(
                "entity_creation_failed", model=self.model.__name__, error=str(e)
            )
            raise
        except Exception as e:
            self.db.rollback()
            database_logger.error(
                "unexpected_error_during_creation",
                model=self.model.__name__,
                error=str(e),
            )
            raise

    @log_database_operation("read")
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Get entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity instance or None if not found
        """
        try:
            stmt = select(self.model).where(self.model.id == id)
            result = self.db.execute(stmt)
            entity = result.scalar_one_or_none()

            return entity

        except Exception as e:
            database_logger.error(
                "entity_retrieval_failed",
                model=self.model.__name__,
                entity_id=id,
                error=str(e),
            )
            raise

    @log_database_operation("read")
    def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """
        Get multiple entities with pagination and filtering.

        Args:
            skip: Number of entities to skip
            limit: Maximum number of entities to return
            filters: Optional filters to apply

        Returns:
            List of entity instances
        """
        try:
            stmt = select(self.model)

            # Apply filters if provided
            if filters:
                stmt = self._apply_filters(stmt, filters)

            stmt = stmt.offset(skip).limit(limit)

            result = self.db.execute(stmt)
            entities = result.scalars().all()

            return entities

        except Exception as e:
            database_logger.error(
                "entities_retrieval_failed", model=self.model.__name__, error=str(e)
            )
            raise

    @log_database_operation("update")
    def update(self, id: int, obj_in: UpdateSchemaType) -> Optional[T]:
        """
        Update an existing entity.

        Args:
            id: Entity ID
            obj_in: Pydantic schema with update data

        Returns:
            Updated entity instance or None if not found
        """
        try:
            # Get existing entity
            db_obj = self.get_by_id(id)
            if not db_obj:
                return None

            # Convert update data to dict, excluding unset values
            update_data = (
                obj_in.model_dump(exclude_unset=True)
                if hasattr(obj_in, "model_dump")
                else obj_in.dict(exclude_unset=True)
            )

            # Update entity attributes
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            self.db.commit()
            self.db.refresh(db_obj)

            return db_obj

        except IntegrityError as e:
            self.db.rollback()
            database_logger.error(
                "entity_update_failed",
                model=self.model.__name__,
                entity_id=id,
                error=str(e),
            )
            raise
        except Exception as e:
            self.db.rollback()
            database_logger.error(
                "unexpected_error_during_update",
                model=self.model.__name__,
                entity_id=id,
                error=str(e),
            )
            raise

    @log_database_operation("delete")
    def delete(self, id: int) -> bool:
        """
        Delete an entity by ID.

        Args:
            id: Entity ID

        Returns:
            True if entity was deleted, False if not found
        """
        try:
            # Check if entity exists
            db_obj = self.get_by_id(id)
            if not db_obj:
                return False

            # Delete entity
            self.db.delete(db_obj)
            self.db.commit()

            return True

        except Exception as e:
            self.db.rollback()
            database_logger.error(
                "entity_deletion_failed",
                model=self.model.__name__,
                entity_id=id,
                error=str(e),
            )
            raise

    @log_database_operation("read")
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities with optional filters.

        Args:
            filters: Optional filters to apply

        Returns:
            Number of entities matching the criteria
        """
        try:
            stmt = select(func.count(self.model.id))

            # Apply filters if provided
            if filters:
                stmt = self._apply_filters(stmt, filters)

            result = self.db.execute(stmt)
            count = result.scalar()

            return count

        except Exception as e:
            database_logger.error(
                "entity_count_failed", model=self.model.__name__, error=str(e)
            )
            raise

    def _apply_filters(self, stmt, filters: Dict[str, Any]):
        """
        Apply filters to a SQLAlchemy statement.

        This method can be overridden by specific repositories
        to implement custom filtering logic.

        Args:
            stmt: SQLAlchemy statement
            filters: Dictionary of filters to apply

        Returns:
            Modified SQLAlchemy statement
        """
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                stmt = stmt.where(getattr(self.model, field) == value)

        return stmt
