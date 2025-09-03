"""encrypt PHI columns"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# Identificadores de la migración
revision: str = "f1b6f3a4c8d7"
down_revision: Union[str, Sequence[str], None] = "e1a1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Modificamos la tabla user_profiles
    with op.batch_alter_table("user_profiles") as batch_op:
        # Eliminamos las columnas numéricas existentes
        batch_op.drop_column("weight_kg")
        batch_op.drop_column("height_cm")
        # Las volvemos a crear como binario para poder cifrarlas
        batch_op.add_column(sa.Column("weight_kg", sa.LargeBinary()))
        batch_op.add_column(sa.Column("height_cm", sa.LargeBinary()))
        # Añadimos la columna medical_conditions también como binaria (nullable)
        batch_op.add_column(
            sa.Column("medical_conditions", sa.LargeBinary(), nullable=True)
        )


def downgrade() -> None:
    # Revertimos los cambios si se deshace la migración
    with op.batch_alter_table("user_profiles") as batch_op:
        # Eliminamos la columna medical_conditions
        batch_op.drop_column("medical_conditions")
        # Y cambiamos de nuevo el tipo de height_cm y weight_kg a flotante
        batch_op.alter_column("height_cm", type_=sa.Float(), existing_nullable=True)
        batch_op.alter_column("weight_kg", type_=sa.Float(), existing_nullable=True)
