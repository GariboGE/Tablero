import pandas as pd
from models.models import Credit, RelatedCredit, Provider, Disposition, db
from sqlalchemy.exc import IntegrityError


def parse_date(val):
    try:
        if pd.notna(val):
            return pd.to_datetime(val, dayfirst=True, errors="coerce").date()
        return None
    except Exception:
        return None


def parse_time(val):
    try:
        return pd.to_datetime(val, errors = "coerce").time() if pd.notna(val) else None
    except Exception:
        return None


def import_csv_to_db(df: pd.DataFrame, session=None):
    """
    Inserta los registros de un DataFrame (CSV) en la base de datos.
    Si hay errores de unicidad (duplicados), los omite y continúa.
    Retorna una tupla: (insertados, omitidos)
    """

    session = session or db.session
    inserted, skipped, updated = 0, 0, 0

    # Eliminar la última fila si parece ser de totales
    last_row = df.tail(1)
    
    contains_totals = last_row.astype(str).apply(
        lambda col: col.str.contains("TOTALES", case=False, na=False)
    ).values.any()


    if contains_totals:
        print("⚠️ Fila de totales detectada y eliminada.")
        df = df.iloc[:-1]

    for _, row in df.iterrows():
        
        try:
            numero_credito = row.get("No. Crédito")
            nuevo_estatus = row.get("Estatus del crédito")

            existing_credit = session.query(Credit).filter_by(
                numero_credito=numero_credito
            ).first()

            if existing_credit:

                # Si el estatus cambió, actualizar
                if existing_credit.estatus_credito != nuevo_estatus:

                    existing_credit.estatus_credito = nuevo_estatus
                    updated += 1

                    # Si quieres marcarlo explícitamente como ignorado
                    if nuevo_estatus == "Cancelado":
                        existing_credit.estatus_credito = "Cancelado"

                    session.commit()
                    print(f"🔄 Crédito {numero_credito} actualizado a estatus {nuevo_estatus}")

                skipped += 1
                continue

            # --- SI NO EXISTE, CREAR NUEVO ---
            credit = Credit(
                tipo_credito=row.get("Tipo de Crédito"),
                fecha_desembolso=parse_date(row.get("Fecha Desembolso")),
                numero_credito=numero_credito,
                empresa=row.get("Empresa"),
                promotor=row.get("Promotor"),
                nombre_cliente=row.get("Nombre del cliente"),
                monto_autorizado=row.get("Monto Autorizado"),
                monto_refinanciar=row.get("Monto a Refinanciar"),
                monto_disponer=row.get("Monto a Disponer"),
                clasificacion_credito=row.get("Clasificación del crédito"),
                nombre_sucursal=row.get("Nombre de la Sucursal"),
                nombre_aval=row.get("Nombre Aval"),
                mes_desembolso=row.get("Mes Desembolso"),
                estatus_credito=nuevo_estatus,
                suma_ref=row.get("Suma REF"),
                suma_proveedores=row.get("Suma Proveedores"),
                monto_crecimiento=row.get("Monto crecimiento"),
                monto_refinanciado=row.get("Monto refinanciado"),
                tipo_comite=row.get("Tipo de Comité"),
                horario_autorizacion=parse_time(row.get("Horario Autorización")),
                usuario_mesa_control=row.get("Usuario Mesa de Control"),
                tipo_disposicion=row.get("Tipo de Disposición"),
                total_dispersiones=row.get("Total Dispersiones"),
                vFirstDueDate=parse_date(row.get("vFirstDueDate")),
                nInterestRateM=row.get("nInterestRateM"),
            )

            session.add(credit)
            session.commit()
            inserted += 1

        except Exception as e:
            session.rollback()
            skipped += 1
            print(f"[ERROR] Registro omitido: {e}")

            # Créditos relacionados
            for i in range(1, 6):
                ref = row.get(f"Referencia Crédito {i}")
                monto = row.get(f"Monto a liquidar.{i}", row.get(f"Monto a liquidar {i}"))
                if pd.notna(ref) or pd.notna(monto):
                    credit.related_credits.append(RelatedCredit(
                        referencia_credito = ref,
                        monto_liquidar = monto
                    ))

            # Proveedores
            for i in range(1, 6):
                prov = row.get(f"Proveedor {i}")
                monto = row.get(f"Monto.{i}", row.get(f"Monto {i}"))
                if pd.notna(prov) or pd.notna(monto):
                    credit.providers.append(Provider(
                        nombre_proveedor = prov,
                        monto = monto
                    ))

            # Disposiciones
            for i in range(1, 6):
                ref = row.get(f"Referencia disposición {i}")
                monto = row.get(f"Monto_disp.{i}", row.get(f"Monto {i}"))
                if pd.notna(ref) or pd.notna(monto):
                    credit.dispositions.append(Disposition(
                        referencia_disposicion = ref,
                        monto = monto
                    ))

            # Intentar guardar el registro
            session.add(credit)
            session.commit()
            inserted += 1

        except IntegrityError:
            session.rollback()
            skipped += 1
        except Exception as e:
            session.rollback()
            skipped += 1
            print(f"[ERROR] Registro omitido por error inesperado: {e}")

    print(f"✅ Datos importados correctamente. Insertados: {inserted}, Actualizados: {updated}, Omitidos: {skipped}")
    return inserted, skipped, updated
