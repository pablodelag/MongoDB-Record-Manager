import reflex as rx

from app.states.explorer_state import ExplorerState


BUTTON = "inline-flex items-center justify-center gap-2 rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm font-medium text-stone-700 transition hover:border-stone-300 hover:bg-stone-50 focus-visible:outline-2 focus-visible:outline-teal-600 disabled:cursor-not-allowed disabled:opacity-40"
PRIMARY = "inline-flex items-center justify-center gap-2 rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-teal-800 focus-visible:outline-2 focus-visible:outline-teal-600 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-40"
INPUT = "w-full rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm text-stone-800 placeholder:text-stone-400 focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-600/10 disabled:opacity-50"


def select_control(content: rx.Component) -> rx.Component:
    return rx.el.div(
        content,
        rx.icon(
            "chevron-down",
            class_name="pointer-events-none absolute right-3 top-3 h-4 w-4 text-stone-400",
        ),
        class_name="relative min-w-0",
    )


def toolbar() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.icon("database", class_name="h-5 w-5 text-teal-800"),
                class_name="flex h-9 w-9 items-center justify-center rounded-xl border border-teal-800/10 bg-teal-800/5",
            ),
            rx.el.div(
                rx.el.span(
                    "MongoDB",
                    class_name="font-semibold tracking-tight text-stone-900",
                ),
                rx.el.span(
                    " / Record explorer", class_name="text-sm text-stone-500"
                ),
            ),
            class_name="flex items-center gap-3",
        ),
        rx.el.div(
            rx.el.span(
                rx.el.span(
                    class_name=rx.cond(
                        ExplorerState.connected,
                        "h-1.5 w-1.5 rounded-full bg-teal-600",
                        "h-1.5 w-1.5 rounded-full bg-stone-400",
                    )
                ),
                rx.cond(
                    ExplorerState.busy,
                    "Working…",
                    rx.cond(
                        ExplorerState.connected, "Connected", "Not connected"
                    ),
                ),
                class_name="hidden items-center gap-2 text-xs text-stone-500 sm:flex",
            ),
            rx.el.button(
                rx.icon(
                    "refresh-cw",
                    class_name=rx.cond(
                        ExplorerState.busy, "h-4 w-4 animate-spin", "h-4 w-4"
                    ),
                ),
                "Refresh",
                on_click=ExplorerState.refresh,
                disabled=ExplorerState.busy,
                class_name=BUTTON,
            ),
            class_name="flex items-center gap-5",
        ),
        class_name="flex shrink-0 items-center justify-between gap-4 border-b border-stone-200 bg-white px-5 py-4 lg:px-7",
    )


def rail() -> rx.Component:
    return rx.el.aside(
        rx.el.div(
            rx.el.p(
                "WORKSPACE",
                class_name="mb-4 text-[10px] font-semibold tracking-[0.16em] text-stone-400",
            ),
            rx.el.form(
                rx.el.label(
                    "Database",
                    html_for="database-select",
                    class_name="mb-2 block text-xs font-medium text-stone-600",
                ),
                select_control(
                    rx.el.select(
                        rx.el.option(
                            "Choose a database", value="", disabled=True
                        ),
                        rx.foreach(
                            ExplorerState.databases,
                            lambda name: rx.el.option(name, value=name),
                        ),
                        name="database",
                        id="database-select",
                        default_value=ExplorerState.database,
                        key=ExplorerState.database,
                        disabled=ExplorerState.busy
                        | (~ExplorerState.connected),
                        class_name="w-full appearance-none rounded-lg border border-stone-200 bg-white py-2.5 pl-3 pr-8 text-sm font-medium text-stone-800 focus:outline-teal-600",
                    )
                ),
                rx.el.button(
                    "Open database",
                    type="submit",
                    disabled=ExplorerState.busy | (~ExplorerState.connected),
                    class_name="mt-2 w-full rounded-lg border border-stone-200 bg-transparent py-2 text-xs font-medium text-stone-600 transition hover:bg-white disabled:opacity-40",
                ),
                on_submit=ExplorerState.select_database,
            ),
            class_name="shrink-0 p-5",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Collections",
                    class_name="text-xs font-semibold text-stone-700",
                ),
                rx.el.span(
                    ExplorerState.visible_collections.length(),
                    class_name="rounded-md bg-stone-200/50 px-1.5 py-0.5 text-[10px] text-stone-500",
                ),
                class_name="mb-3 flex items-center justify-between",
            ),
            rx.el.div(
                rx.icon(
                    "search",
                    class_name="absolute left-3 top-2.5 h-3.5 w-3.5 text-stone-400",
                ),
                rx.el.input(
                    placeholder="Find a collection…",
                    aria_label="Find a collection",
                    default_value=ExplorerState.collection_search,
                    key=ExplorerState.database,
                    on_change=ExplorerState.search_collections.debounce(300),
                    class_name="w-full rounded-lg border border-stone-200 bg-white py-2 pl-8 pr-3 text-xs text-stone-700 placeholder:text-stone-400 focus:outline-teal-600",
                ),
                class_name="relative",
            ),
            class_name="shrink-0 px-5 pb-3",
        ),
        rx.el.nav(
            rx.foreach(
                ExplorerState.visible_collections,
                lambda name: rx.el.button(
                    rx.icon("layers-2", class_name="h-4 w-4 shrink-0"),
                    rx.el.span(name, class_name="truncate"),
                    rx.cond(
                        ExplorerState.collection == name,
                        rx.icon(
                            "chevron-right",
                            class_name="ml-auto h-3.5 w-3.5 shrink-0",
                        ),
                    ),
                    on_click=lambda: ExplorerState.select_collection(name),
                    disabled=ExplorerState.busy | (~ExplorerState.connected),
                    title=name,
                    class_name=rx.cond(
                        ExplorerState.collection == name,
                        "flex w-full items-center gap-2.5 rounded-lg border border-teal-700/10 bg-teal-700/8 px-3 py-2.5 text-left text-sm font-medium text-teal-800 disabled:opacity-50",
                        "flex w-full items-center gap-2.5 rounded-lg border border-transparent bg-transparent px-3 py-2.5 text-left text-sm text-stone-600 transition hover:bg-stone-200/50 disabled:opacity-50",
                    ),
                ),
            ),
            rx.cond(
                ExplorerState.visible_collections.length() == 0,
                rx.el.p(
                    rx.cond(
                        ExplorerState.database != "",
                        "No collections to display.",
                        "Open a database to browse its collections.",
                    ),
                    class_name="px-3 py-3 text-xs leading-relaxed text-stone-400",
                ),
            ),
            class_name="flex max-h-48 min-h-0 flex-1 flex-col gap-1 overflow-y-auto px-3 pb-4 md:max-h-none",
        ),
        rx.el.div(
            rx.icon(
                "shield-check", class_name="h-4 w-4 shrink-0 text-teal-700"
            ),
            rx.el.p(
                "Your existing data. No seeded records.",
                class_name="text-[11px] leading-relaxed text-stone-500",
            ),
            class_name="hidden shrink-0 items-center gap-2 border-t border-stone-200 p-5 md:flex",
        ),
        class_name="flex w-full shrink-0 flex-col border-b border-stone-200 bg-[#f4f3ef] md:h-full md:w-60 md:border-r md:border-b-0 lg:w-64",
    )


def filters() -> rx.Component:
    return rx.el.div(
        rx.el.form(
            rx.el.div(
                rx.icon("list-filter", class_name="h-4 w-4 text-teal-700"),
                rx.el.span(
                    "Filter", class_name="text-xs font-semibold text-stone-600"
                ),
                class_name="flex items-center gap-2 pr-1",
            ),
            rx.el.input(
                name="field",
                placeholder="Field or nested.path",
                aria_label="Filter field",
                list="document-fields",
                default_value=ExplorerState.field,
                key=ExplorerState.field,
                disabled=ExplorerState.busy | (ExplorerState.collection == ""),
                class_name=INPUT,
            ),
            rx.el.datalist(
                rx.foreach(
                    ExplorerState.columns,
                    lambda column: rx.el.option(value=column),
                ),
                id="document-fields",
            ),
            select_control(
                rx.el.select(
                    rx.foreach(
                        [
                            "contains",
                            "equals",
                            "not equals",
                            "greater than",
                            "less than",
                        ],
                        lambda operator: rx.el.option(operator, value=operator),
                    ),
                    name="operator",
                    aria_label="Filter operator",
                    default_value=ExplorerState.operator,
                    key=ExplorerState.operator,
                    disabled=ExplorerState.busy
                    | (ExplorerState.collection == ""),
                    class_name="w-full appearance-none rounded-lg border border-stone-200 bg-white py-2 pl-3 pr-9 text-sm text-stone-700 focus:outline-teal-600",
                )
            ),
            rx.el.input(
                name="value",
                placeholder="Value or Extended JSON",
                aria_label="Filter value",
                default_value=ExplorerState.filter_value,
                key=ExplorerState.filter_value,
                disabled=ExplorerState.busy | (ExplorerState.collection == ""),
                class_name=INPUT,
            ),
            rx.el.button(
                "Apply",
                type="submit",
                disabled=ExplorerState.busy | (ExplorerState.collection == ""),
                class_name=BUTTON,
            ),
            rx.el.button(
                "Clear",
                type="button",
                on_click=ExplorerState.clear_filter,
                disabled=ExplorerState.busy | (ExplorerState.collection == ""),
                class_name="px-2 py-2 text-xs font-medium text-stone-500 transition hover:text-teal-700 disabled:opacity-40",
            ),
            on_submit=ExplorerState.apply_filter,
            class_name="grid grid-cols-2 items-center gap-2 lg:grid-cols-[auto_minmax(120px,1fr)_160px_minmax(150px,1.3fr)_auto_auto]",
        ),
        rx.el.p(
            "Contains matches text, case-insensitively. Other operators accept JSON numbers, booleans, null, and BSON Extended JSON; plain text stays a string.",
            class_name="mt-3 text-[11px] leading-relaxed text-stone-400",
        ),
        class_name="border-b border-stone-200 bg-stone-50/60 p-4",
    )


def records_table() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        rx.foreach(
                            ExplorerState.columns,
                            lambda column: rx.el.th(
                                rx.el.div(
                                    rx.icon(
                                        "hash",
                                        class_name="h-3 w-3 text-stone-400",
                                    ),
                                    column,
                                    class_name="flex items-center gap-2",
                                ),
                                class_name="whitespace-nowrap border-b border-stone-200 bg-[#fafaf8] px-5 py-4 text-left text-xs font-medium text-stone-500",
                            ),
                        ),
                        rx.el.th(
                            "Record",
                            class_name="border-b border-stone-200 bg-[#fafaf8] px-5 py-4 text-right text-xs font-medium text-stone-500",
                        ),
                    )
                ),
                rx.el.tbody(
                    rx.foreach(
                        ExplorerState.rows,
                        lambda row, index: rx.el.tr(
                            rx.foreach(
                                ExplorerState.columns,
                                lambda column: rx.el.td(
                                    rx.el.div(
                                        row["cells"].get(column, "—"),
                                        title=row["cells"].get(column, "—"),
                                        class_name="max-w-72 truncate font-mono text-xs text-stone-700",
                                    ),
                                    class_name="border-b border-stone-100 px-5 py-5",
                                ),
                            ),
                            rx.el.td(
                                rx.el.button(
                                    rx.icon("braces", class_name="h-3.5 w-3.5"),
                                    "View",
                                    on_click=lambda: ExplorerState.open_record(
                                        index
                                    ),
                                    disabled=ExplorerState.busy,
                                    class_name="inline-flex items-center gap-2 rounded-md bg-transparent px-2 py-1 text-xs font-medium text-teal-700 hover:bg-teal-50 disabled:opacity-40",
                                ),
                                class_name="border-b border-stone-100 px-5 py-4 text-right",
                            ),
                            key=row["identifier"],
                            class_name="bg-white transition even:bg-stone-50/40 hover:bg-teal-50/40",
                        ),
                    )
                ),
                class_name="table-auto w-full",
            ),
            class_name="w-full overflow-x-auto",
        ),
        class_name="min-h-72 w-full overflow-hidden bg-white",
    )


def centered_state(icon: str, title: str, description: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-6 w-6 text-teal-700"),
            class_name="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl border border-stone-200 bg-[#f7f7f3]",
        ),
        rx.el.h3(
            title,
            class_name="text-base font-semibold tracking-tight text-stone-800",
        ),
        rx.el.p(
            description,
            class_name="mt-2 max-w-md text-center text-sm leading-6 text-stone-500",
        ),
        class_name="flex min-h-80 flex-col items-center justify-center px-6 py-12",
    )


def connection_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("unplug", class_name="h-6 w-6 text-stone-600"),
                class_name="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl border border-stone-200 bg-[#f5f4ef]",
            ),
            rx.el.span(
                "CONNECTION UNAVAILABLE",
                class_name="mb-3 text-[10px] font-semibold tracking-[0.16em] text-stone-400",
            ),
            rx.el.h3(
                "Let’s get your database connected",
                class_name="text-xl font-semibold tracking-tight text-stone-800",
            ),
            rx.el.p(
                "MongoDB could not establish a secure connection. Your records have not been loaded or changed.",
                class_name="mt-3 max-w-md text-sm leading-6 text-stone-500",
            ),
            rx.el.div(
                rx.icon(
                    "info", class_name="mt-0.5 h-4 w-4 shrink-0 text-teal-700"
                ),
                rx.el.p(
                    "Check database network access, the IP allowlist, and TLS settings. Then retry the connection.",
                    class_name="text-xs leading-5 text-stone-600",
                ),
                class_name="my-6 flex max-w-md gap-3 rounded-xl border border-stone-200 bg-[#f8f8f4] p-4 text-left",
            ),
            rx.el.button(
                rx.icon("refresh-cw", class_name="h-4 w-4"),
                "Retry connection",
                on_click=ExplorerState.connect,
                disabled=ExplorerState.busy,
                class_name=PRIMARY,
            ),
            rx.el.p(
                "Connection details stay on the server.",
                class_name="mt-4 text-[11px] text-stone-400",
            ),
            class_name="flex flex-col items-center text-center",
        ),
        class_name="flex min-h-[430px] items-center justify-center bg-white px-5 py-12",
    )


def pagination() -> rx.Component:
    return rx.el.div(
        rx.el.span(
            ExplorerState.range_label, class_name="text-xs text-stone-500"
        ),
        rx.el.div(
            rx.el.form(
                rx.el.span("Rows", class_name="text-xs text-stone-400"),
                select_control(
                    rx.el.select(
                        rx.foreach(
                            ["10", "25", "50", "100"],
                            lambda size: rx.el.option(size, value=size),
                        ),
                        name="limit",
                        aria_label="Rows per page",
                        default_value=ExplorerState.limit.to_string(),
                        key=ExplorerState.limit,
                        class_name="appearance-none rounded-md border border-stone-200 bg-white py-1.5 pl-2 pr-8 text-xs text-stone-700",
                    )
                ),
                rx.el.button(
                    "Set",
                    type="submit",
                    disabled=ExplorerState.busy
                    | (ExplorerState.collection == ""),
                    class_name="text-xs text-stone-500 hover:text-teal-700 disabled:opacity-40",
                ),
                on_submit=ExplorerState.page_size,
                class_name="hidden items-center gap-2 sm:flex",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("chevron-left", class_name="h-4 w-4"),
                    aria_label="Previous page",
                    on_click=lambda: ExplorerState.paginate(-1),
                    disabled=ExplorerState.busy | (ExplorerState.page == 0),
                    class_name=BUTTON,
                ),
                rx.el.span(
                    f"{ExplorerState.page + 1} / {ExplorerState.pages}",
                    class_name="min-w-12 text-center text-xs text-stone-500",
                ),
                rx.el.button(
                    rx.icon("chevron-right", class_name="h-4 w-4"),
                    aria_label="Next page",
                    on_click=lambda: ExplorerState.paginate(1),
                    disabled=ExplorerState.busy
                    | (ExplorerState.page + 1 >= ExplorerState.pages),
                    class_name=BUTTON,
                ),
                class_name="flex items-center gap-2",
            ),
            class_name="flex items-center gap-5",
        ),
        class_name="flex flex-wrap items-center justify-between gap-3 border-t border-stone-200 bg-white px-5 py-4",
    )


def record_modal() -> rx.Component:
    return rx.cond(
        ExplorerState.modal != "",
        rx.el.div(
            rx.el.section(
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.icon(
                                "braces", class_name="h-4 w-4 text-teal-700"
                            ),
                            rx.el.h2(
                                rx.match(
                                    ExplorerState.modal,
                                    ("add", "Add record"),
                                    ("edit", "Edit record"),
                                    ("delete", "Delete record?"),
                                    "Record JSON",
                                ),
                                id="record-dialog-title",
                                class_name="text-lg font-semibold text-stone-900",
                            ),
                            class_name="flex items-center gap-2",
                        ),
                        rx.el.p(
                            f"{ExplorerState.database} / {ExplorerState.collection}",
                            class_name="mt-1 truncate text-xs text-stone-500",
                        ),
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="h-5 w-5"),
                        aria_label="Close dialog",
                        on_click=ExplorerState.close_modal,
                        disabled=ExplorerState.busy,
                        class_name="rounded-lg bg-transparent p-2 text-stone-400 hover:bg-stone-100 hover:text-stone-800 disabled:opacity-30",
                    ),
                    class_name="flex items-center justify-between border-b border-stone-200 p-5",
                ),
                rx.cond(
                    ExplorerState.modal_error != "",
                    rx.el.div(
                        rx.icon("circle-alert", class_name="h-4 w-4 shrink-0"),
                        ExplorerState.modal_error,
                        role="alert",
                        class_name="mx-5 mt-4 flex items-start gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-700",
                    ),
                ),
                rx.match(
                    ExplorerState.modal,
                    (
                        "view",
                        rx.el.div(
                            rx.el.p(
                                "Canonical Extended JSON preserves ObjectIds, dates, and other BSON types.",
                                class_name="mb-3 text-xs text-stone-500",
                            ),
                            rx.el.pre(
                                ExplorerState.editor,
                                class_name="max-h-[52dvh] overflow-auto whitespace-pre-wrap break-all rounded-xl border border-stone-200 bg-[#f8f8f5] p-5 font-mono text-xs leading-6 text-stone-800",
                            ),
                            rx.el.div(
                                rx.el.button(
                                    rx.icon("trash-2", class_name="h-4 w-4"),
                                    "Delete",
                                    on_click=ExplorerState.confirm_delete,
                                    disabled=ExplorerState.busy,
                                    class_name="inline-flex items-center gap-2 rounded-lg bg-transparent px-3 py-2 text-sm text-red-600 hover:bg-red-50 disabled:opacity-40",
                                ),
                                rx.el.button(
                                    rx.icon("pencil", class_name="h-4 w-4"),
                                    "Edit JSON",
                                    on_click=ExplorerState.enable_edit,
                                    disabled=ExplorerState.busy,
                                    class_name=PRIMARY,
                                ),
                                class_name="mt-5 flex justify-between",
                            ),
                            class_name="p-5",
                        ),
                    ),
                    (
                        "delete",
                        rx.el.div(
                            rx.el.div(
                                rx.icon(
                                    "triangle-alert",
                                    class_name="h-5 w-5 shrink-0 text-red-600",
                                ),
                                rx.el.p(
                                    "This permanently deletes the selected record from this collection. This action cannot be undone.",
                                    class_name="text-sm leading-6 text-stone-700",
                                ),
                                class_name="flex gap-3",
                            ),
                            rx.el.pre(
                                ExplorerState.editor,
                                class_name="mt-4 max-h-52 overflow-auto whitespace-pre-wrap break-all rounded-lg border border-stone-200 bg-stone-50 p-4 font-mono text-xs text-stone-600",
                            ),
                            rx.el.div(
                                rx.el.button(
                                    "Cancel",
                                    on_click=ExplorerState.close_modal,
                                    disabled=ExplorerState.busy,
                                    class_name=BUTTON,
                                ),
                                rx.el.button(
                                    rx.cond(
                                        ExplorerState.busy,
                                        "Deleting…",
                                        "Delete permanently",
                                    ),
                                    on_click=ExplorerState.delete_record,
                                    disabled=ExplorerState.busy,
                                    class_name="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-40",
                                ),
                                class_name="mt-5 flex justify-end gap-3",
                            ),
                            class_name="p-5",
                        ),
                    ),
                    rx.el.form(
                        rx.el.p(
                            rx.cond(
                                ExplorerState.modal == "add",
                                "Enter one JSON object. Omit _id to let MongoDB generate it.",
                                "Saving replaces the document. Keep _id and its BSON type unchanged.",
                            ),
                            class_name="mb-2 text-xs leading-5 text-stone-600",
                        ),
                        rx.el.p(
                            "Keep Extended JSON wrappers to preserve BSON types. Concurrent changes are checked before saving.",
                            class_name="mb-4 text-[11px] text-stone-400",
                        ),
                        rx.el.textarea(
                            name="document",
                            aria_label="Record JSON",
                            default_value=ExplorerState.editor,
                            key=ExplorerState.editor_revision,
                            required=True,
                            spell_check=False,
                            disabled=ExplorerState.busy,
                            class_name="h-[42dvh] min-h-52 w-full resize-y rounded-xl border border-stone-200 bg-[#f8f8f5] p-4 font-mono text-xs leading-6 text-stone-800 focus:border-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-700/10 disabled:opacity-50",
                        ),
                        rx.el.div(
                            rx.el.button(
                                "Cancel",
                                type="button",
                                on_click=ExplorerState.close_modal,
                                disabled=ExplorerState.busy,
                                class_name=BUTTON,
                            ),
                            rx.el.button(
                                rx.cond(
                                    ExplorerState.busy,
                                    "Saving…",
                                    rx.cond(
                                        ExplorerState.modal == "add",
                                        "Insert record",
                                        "Save changes",
                                    ),
                                ),
                                type="submit",
                                disabled=ExplorerState.busy,
                                class_name=PRIMARY,
                            ),
                            class_name="mt-5 flex justify-end gap-3",
                        ),
                        on_submit=ExplorerState.save_record,
                        class_name="p-5",
                    ),
                ),
                role="dialog",
                aria_modal=True,
                aria_labelledby="record-dialog-title",
                class_name="max-h-[90dvh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-stone-200 bg-white",
            ),
            class_name="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/35 p-4 backdrop-blur-xs",
        ),
    )


def workbench() -> rx.Component:
    return rx.el.div(
        toolbar(),
        rx.el.div(
            rail(),
            rx.el.main(
                rx.el.div(
                    rx.el.div(
                        rx.el.p(
                            "DATA WORKBENCH",
                            class_name="mb-3 text-[10px] font-semibold tracking-[0.18em] text-teal-700",
                        ),
                        rx.el.h1(
                            rx.cond(
                                ExplorerState.collection != "",
                                ExplorerState.collection,
                                "Record explorer",
                            ),
                            class_name="break-all text-3xl font-semibold tracking-tight text-stone-900",
                        ),
                        rx.el.p(
                            "Browse, inspect, and carefully edit your MongoDB documents.",
                            class_name="mt-2 text-sm leading-6 text-stone-500",
                        ),
                    ),
                    rx.el.button(
                        rx.icon("plus", class_name="h-4 w-4"),
                        "Add record",
                        on_click=ExplorerState.new_record,
                        disabled=ExplorerState.busy
                        | (~ExplorerState.connected)
                        | (ExplorerState.collection == ""),
                        class_name=PRIMARY,
                    ),
                    class_name="mb-7 flex flex-wrap items-center justify-between gap-5",
                ),
                rx.cond(
                    ExplorerState.success != "",
                    rx.el.div(
                        rx.icon("circle-check", class_name="h-4 w-4"),
                        ExplorerState.success,
                        role="status",
                        class_name="mb-4 flex items-center gap-2 rounded-lg border border-teal-100 bg-teal-50 px-4 py-3 text-sm text-teal-800",
                    ),
                ),
                rx.cond(
                    (ExplorerState.error != "")
                    & (~ExplorerState.connection_error),
                    rx.el.div(
                        rx.icon("circle-alert", class_name="h-4 w-4 shrink-0"),
                        ExplorerState.error,
                        role="alert",
                        class_name="mb-4 flex items-center gap-2 rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700",
                    ),
                ),
                rx.el.section(
                    rx.el.div(
                        rx.el.div(
                            rx.icon(
                                "table-2", class_name="h-4 w-4 text-teal-700"
                            ),
                            rx.el.h2(
                                "Documents",
                                class_name="text-sm font-semibold text-stone-800",
                            ),
                            class_name="flex items-center gap-2",
                        ),
                        rx.el.span(
                            "LIVE DATABASE",
                            class_name="text-[10px] font-medium tracking-widest text-stone-400",
                        ),
                        class_name="flex items-center justify-between border-b border-stone-200 bg-white px-5 py-4",
                    ),
                    filters(),
                    rx.cond(
                        ExplorerState.busy,
                        rx.el.div(
                            rx.icon(
                                "loader-circle",
                                class_name="mb-4 h-6 w-6 animate-spin text-teal-700",
                            ),
                            rx.el.p(
                                "Loading from MongoDB…",
                                class_name="text-sm text-stone-500",
                            ),
                            rx.el.div(
                                class_name="mt-7 h-3 w-2/3 animate-pulse rounded-md bg-stone-100"
                            ),
                            rx.el.div(
                                class_name="mt-4 h-3 w-1/2 animate-pulse rounded-md bg-stone-100"
                            ),
                            role="status",
                            class_name="flex min-h-80 flex-col items-center justify-center bg-white px-8 py-10",
                        ),
                        rx.cond(
                            ExplorerState.connection_error,
                            connection_panel(),
                            rx.cond(
                                ExplorerState.collection == "",
                                centered_state(
                                    "database",
                                    "Your data, in focus",
                                    "Choose a database and a collection from the workspace to explore its records. Nothing is created or changed until you explicitly save.",
                                ),
                                rx.cond(
                                    ExplorerState.rows.length() > 0,
                                    records_table(),
                                    centered_state(
                                        "search",
                                        "No records to display",
                                        "This collection is empty, or no documents match your filter. Clear the filter, refresh, or add a record when you’re ready.",
                                    ),
                                ),
                            ),
                        ),
                    ),
                    pagination(),
                    class_name="w-full overflow-hidden rounded-xl border border-stone-200 bg-white",
                ),
                rx.el.div(
                    rx.el.p(
                        rx.icon("lock-keyhole", class_name="h-3 w-3"),
                        "BSON-safe editing · Explicit saves · Selected collection only",
                        class_name="flex items-center gap-2 text-[11px] text-stone-400",
                    ),
                    rx.el.p(
                        "Columns reflect documents on the current page.",
                        class_name="text-[11px] text-stone-400",
                    ),
                    class_name="mt-4 flex flex-wrap justify-between gap-2",
                ),
                class_name="min-w-0 w-full flex-1 overflow-y-auto bg-[#faf9f6] p-5 md:p-7 lg:p-9",
            ),
            class_name="flex min-h-0 flex-1 flex-col overflow-y-auto md:flex-row md:overflow-hidden",
        ),
        record_modal(),
        class_name="flex h-dvh w-full flex-col overflow-hidden bg-[#faf9f6] font-['Inter'] text-stone-800",
    )
