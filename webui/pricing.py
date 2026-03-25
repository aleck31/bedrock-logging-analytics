"""Pricing Settings page."""

from datetime import datetime, timezone

from nicegui import ui
from webui import data


@ui.page("/pricing")
def pricing_page():
    ui.dark_mode(False)
    modified = {}  # model_id → {input_per_1k, output_per_1k, effective_date}

    # ── Header ──
    with ui.header().classes("bg-white text-gray-800 shadow-sm items-center px-6"):
        ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props("flat round")
        ui.label("Pricing Settings").classes("text-xl font-bold ml-2")
        ui.space()
        sync_info = data.get_pricing_sync_info()
        if sync_info:
            synced_at = sync_info.get("synced_at", "")
            updated = int(sync_info.get("models_updated", 0))
            skipped = int(sync_info.get("models_skipped", 0))
            ui.label(f"Last sync: {synced_at}  |  {updated} updated, {skipped} unchanged").classes("text-sm text-gray-500")

        update_btn = ui.button("Apply Changes", icon="save", on_click=lambda: apply_changes())
        update_btn.props("flat color=primary").classes("ml-2")
        update_btn.set_visibility(False)

    models = data.get_all_pricing()

    # ── Edit dialog ──
    with ui.dialog() as dialog, ui.card().classes("min-w-[400px]"):
        ui.label("Edit Pricing").classes("text-lg font-semibold")
        dlg_model = ui.label("").classes("text-sm text-gray-500 mb-2")
        dlg_input = ui.number(label="Input $/1K tokens", format="%.6f").classes("w-full")
        dlg_output = ui.number(label="Output $/1K tokens", format="%.6f").classes("w-full mt-2")
        dlg_date = ui.input(label="Effective Date (ISO 8601)").classes("w-full mt-2")
        with ui.row().classes("w-full justify-end mt-4 gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Save", on_click=lambda: save_edit()).props("color=primary")

    edit_ctx = {}  # holds current editing row

    def open_edit(row):
        edit_ctx["row"] = row
        dlg_model.text = row["model_id"]
        dlg_input.value = float(row["input_per_1k"])
        dlg_output.value = float(row["output_per_1k"])
        dlg_date.value = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        dialog.open()

    def save_edit():
        row = edit_ctx["row"]
        model_id = row["model_id"]
        new_input = dlg_input.value or 0
        new_output = dlg_output.value or 0
        new_date = dlg_date.value or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Track modification
        modified[model_id] = {
            "input_per_1k": new_input,
            "output_per_1k": new_output,
            "effective_date": new_date,
        }

        # Update table row display
        for r in table.rows:
            if r["model_id"] == model_id:
                r["input_per_1k"] = f"{new_input:.6f}"
                r["output_per_1k"] = f"{new_output:.6f}"
                r["effective_date"] = new_date
                r["source"] = "manual *"
                break
        table.update()
        update_btn.set_visibility(True)
        badge.text = f"{len(modified)} modified"
        badge.set_visibility(True)
        dialog.close()

    def apply_changes():
        for model_id, vals in modified.items():
            data.save_pricing(model_id, vals["input_per_1k"], vals["output_per_1k"], vals["effective_date"])
        ui.notify(f"Saved {len(modified)} pricing updates", type="positive")
        modified.clear()
        update_btn.set_visibility(False)
        badge.set_visibility(False)

    # ── Table ──
    with ui.column().classes("max-w-6xl mx-auto p-6 w-full"):
        with ui.row().classes("w-full items-center justify-between mb-2"):
            with ui.row().classes("items-center gap-2"):
                ui.label(f"{len(models)} models").classes("text-sm text-gray-500")
                badge = ui.badge("0 modified", color="orange").props("outline")
                badge.set_visibility(False)
            search = ui.input(placeholder="Filter models...").props("dense outlined clearable").classes("w-64")

        columns = [
            {"name": "model_id", "label": "Model ID", "field": "model_id", "align": "left", "sortable": True},
            {"name": "input_per_1k", "label": "Input $/1K tokens", "field": "input_per_1k", "sortable": True},
            {"name": "output_per_1k", "label": "Output $/1K tokens", "field": "output_per_1k", "sortable": True},
            {"name": "effective_date", "label": "Effective Date", "field": "effective_date", "sortable": True},
            {"name": "source", "label": "Source", "field": "source", "sortable": True},
        ]
        rows = [{
            "model_id": m["model_id"],
            "input_per_1k": f'{m["input_per_1k"]:.6f}',
            "output_per_1k": f'{m["output_per_1k"]:.6f}',
            "effective_date": m["effective_date"],
            "source": m["source"],
        } for m in models]

        table = ui.table(columns=columns, rows=rows, row_key="model_id", pagination=20).classes(
            "w-full"
        ).props('dense flat')
        table.on("rowClick", lambda e: open_edit(e.args[1]))
        search.bind_value_to(table, "filter")
