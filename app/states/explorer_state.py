import reflex as rx

import asyncio
import os
import re
from typing import Any, TypedDict

from bson import BSON, json_util
from pymongo import MongoClient
from pymongo.errors import (
    ConfigurationError,
    ConnectionFailure,
    DuplicateKeyError,
    OperationFailure,
)

import logging


class RecordRow(TypedDict):
    cells: dict[str, str]
    identifier: str


def decode_document(text: str) -> dict:
    if len(text.encode("utf-8")) > 16_000_000:
        raise ValueError("Document exceeds the BSON size limit.")
    try:
        document = json_util.loads(text)
        if not isinstance(document, dict):
            raise ValueError()
        BSON.encode(document)
    except Exception:
        raise ValueError(
            "Enter a valid JSON object with valid MongoDB Extended JSON values."
        ) from None
    return document


def build_filter(field: str, operator: str, value: str) -> dict:
    if not field:
        return {}
    if (
        any(not part or part.startswith("$") for part in field.split("."))
        or "\x00" in field
    ):
        raise ValueError(
            "Use a valid field name or dotted field path, without $ operators."
        )
    if operator == "contains":
        return {field: {"$regex": re.escape(value), "$options": "i"}}
    try:
        parsed = json_util.loads(value)
    except Exception:
        logging.exception("Unexpected error")
        parsed = value
    operators = {
        "equals": "$eq",
        "not equals": "$ne",
        "greater than": "$gt",
        "less than": "$lt",
    }
    if operator not in operators:
        raise ValueError("Choose a supported filter operator.")
    return {field: {operators[operator]: parsed}}


def perform_operation(
    operation: str, context: dict[str, str | int]
) -> dict[str, Any]:
    uri = os.environ.get("MONGODB_URI", "")
    if not uri:
        raise ConfigurationError("Connection unavailable")
    with MongoClient(
        uri,
        serverSelectionTimeoutMS=7000,
        connectTimeoutMS=7000,
        socketTimeoutMS=15000,
    ) as client:
        database_name = str(context["database"])
        collection_name = str(context["collection"])
        if operation == "connect":
            client.admin.command("ping")
            try:
                default = client.get_default_database()
            except ConfigurationError:
                logging.exception("Unexpected error")
                default = None
            if default is not None:
                names = [default.name]
                database_name = default.name
            else:
                names = sorted(
                    name
                    for name in client.list_database_names(
                        authorizedDatabases=True
                    )
                    if name not in {"admin", "local", "config"}
                )
                database_name = ""
            collections = (
                sorted(client[database_name].list_collection_names())
                if database_name
                else []
            )
            return {
                "databases": names,
                "database": database_name,
                "collections": collections,
            }
        try:
            default = client.get_default_database()
        except ConfigurationError:
            logging.exception("Unexpected error")
            default = None
        allowed = (
            [default.name]
            if default is not None
            else [
                name
                for name in client.list_database_names(authorizedDatabases=True)
                if name not in {"admin", "local", "config"}
            ]
        )
        if not database_name or database_name not in allowed:
            raise ValueError("Select an accessible database before continuing.")
        database = client[database_name]
        collections = sorted(database.list_collection_names())
        if operation == "database":
            return {"collections": collections}
        if (
            not collection_name
            or collection_name not in collections
            or collection_name.startswith("system.")
        ):
            raise ValueError(
                "Select an accessible, non-system collection before continuing."
            )
        collection = database[collection_name]
        if operation == "records":
            query = build_filter(
                str(context["field"]),
                str(context["operator"]),
                str(context["value"]),
            )
            limit = int(context["limit"])
            total = collection.count_documents(query, maxTimeMS=10000)
            page = min(int(context["page"]), max(0, (total - 1) // limit))
            documents = list(
                collection.find(query)
                .sort("_id", 1)
                .skip(page * limit)
                .limit(limit)
                .max_time_ms(10000)
            )
            columns = list(
                dict.fromkeys(key for document in documents for key in document)
            )
            if "_id" in columns:
                columns.remove("_id")
                columns.insert(0, "_id")
            rows = []
            for document in documents:
                cells = {}
                for key in columns:
                    if key not in document:
                        cells[key] = "—"
                    elif isinstance(document[key], str):
                        cells[key] = document[key]
                    else:
                        cells[key] = json_util.dumps(
                            document[key],
                            json_options=json_util.CANONICAL_JSON_OPTIONS,
                            ensure_ascii=False,
                        )
                rows.append(
                    {
                        "cells": cells,
                        "identifier": json_util.dumps(
                            document.get("_id"),
                            json_options=json_util.CANONICAL_JSON_OPTIONS,
                        ),
                    }
                )
            return {
                "rows": rows,
                "columns": columns,
                "documents": [
                    json_util.dumps(
                        doc, json_options=json_util.CANONICAL_JSON_OPTIONS
                    )
                    for doc in documents
                ],
                "total": total,
                "page": page,
            }
        if operation == "add":
            collection.insert_one(decode_document(str(context["editor"])))
            return {}
        original = decode_document(str(context["target"]))
        if "_id" not in original:
            raise ValueError(
                "This record has no usable identifier. Refresh and try again."
            )
        identity = {"_id": {"$eq": original["_id"]}}
        if operation == "open":
            document = collection.find_one(identity, max_time_ms=10000)
            if document is None:
                raise ValueError(
                    "This record no longer exists. Refresh the collection."
                )
            return {
                "document": json_util.dumps(
                    document,
                    indent=2,
                    ensure_ascii=False,
                    json_options=json_util.CANONICAL_JSON_OPTIONS,
                )
            }
        predicate = {
            "$and": [
                identity,
                {"$expr": {"$eq": ["$$ROOT", {"$literal": original}]}},
            ]
        }
        if operation == "edit":
            document = decode_document(str(context["editor"]))
            if "_id" not in document or BSON.encode(
                {"_id": document["_id"]}
            ) != BSON.encode({"_id": original["_id"]}):
                raise ValueError(
                    "The _id is immutable. Keep its original value and BSON type."
                )
            result = collection.replace_one(predicate, document)
            if result.matched_count != 1:
                raise ValueError(
                    "The record changed or was deleted. Close the editor, refresh, and reopen it."
                )
        elif operation == "delete":
            result = collection.delete_one(predicate)
            if result.deleted_count != 1:
                raise ValueError(
                    "The record changed or was deleted. Refresh and review it before deleting."
                )
        else:
            raise ValueError("Unsupported operation.")
        return {}


class ExplorerState(rx.State):
    databases: list[str] = []
    database: str = ""
    collections: list[str] = []
    collection: str = ""
    collection_search: str = ""
    rows: list[RecordRow] = []
    columns: list[str] = []
    total: int = 0
    page: int = 0
    limit: int = 25
    field: str = ""
    operator: str = "contains"
    filter_value: str = ""
    busy: bool = False
    connected: bool = False
    connection_error: bool = False
    error: str = ""
    success: str = ""
    modal: str = ""
    editor: str = ""
    editor_revision: int = 0
    modal_error: str = ""
    _documents: list[str] = []
    _target: str = ""
    _target_database: str = ""
    _target_collection: str = ""
    _operation: str = ""

    @rx.var
    def visible_collections(self) -> list[str]:
        return [
            name
            for name in self.collections
            if not name.startswith("system.")
            and self.collection_search.lower() in name.lower()
        ]

    @rx.var
    def pages(self) -> int:
        return max(1, (self.total + self.limit - 1) // self.limit)

    @rx.var
    def range_label(self) -> str:
        if not self.total:
            return "0 records"
        return f"{self.page * self.limit + 1}–{min((self.page + 1) * self.limit, self.total):,} of {self.total:,} records"

    def _start(self, operation: str):
        self.busy = True
        self.error = ""
        self.modal_error = ""
        self.success = ""
        self._operation = operation

    def _clear_records(self):
        self.rows = []
        self.columns = []
        self._documents = []
        self.page = 0
        self.total = 0

    @rx.event
    def connect(self):
        if self.busy:
            return
        self.modal = ""
        self.connected = False
        self.connection_error = False
        self.databases = []
        self.collections = []
        self.database = ""
        self.collection = ""
        self._clear_records()
        self._start("connect")
        yield ExplorerState.run_operation

    @rx.event
    def select_database(self, data: dict[str, Any]):
        name = str(data.get("database", ""))
        if self.busy or name not in self.databases:
            return
        self.database = name
        self.collection = ""
        self.collections = []
        self.collection_search = ""
        self.modal = ""
        self.field = ""
        self.filter_value = ""
        self._clear_records()
        self._start("database")
        yield ExplorerState.run_operation

    @rx.event
    def select_collection(self, name: str):
        if (
            self.busy
            or name not in self.collections
            or name.startswith("system.")
        ):
            return
        self.collection = name
        self.modal = ""
        self.field = ""
        self.filter_value = ""
        self._clear_records()
        self._start("records")
        yield ExplorerState.run_operation

    @rx.event
    def search_collections(self, value: str):
        self.collection_search = value

    @rx.event
    def refresh(self):
        if self.busy:
            return
        if not self.connected:
            yield ExplorerState.connect
            return
        self._start(
            "records"
            if self.collection
            else "database"
            if self.database
            else "connect"
        )
        yield ExplorerState.run_operation

    @rx.event
    def apply_filter(self, data: dict[str, Any]):
        if self.busy or not self.collection:
            return
        self.field = str(data.get("field", "")).strip()
        self.operator = str(data.get("operator", "contains"))
        self.filter_value = str(data.get("value", ""))
        if not self.field:
            self.error = (
                "Enter a field to filter, or use Clear to show all records."
            )
            return
        self.page = 0
        self._start("records")
        yield ExplorerState.run_operation

    @rx.event
    def clear_filter(self):
        if self.busy or not self.collection:
            return
        self.field = ""
        self.filter_value = ""
        self.page = 0
        self._start("records")
        yield ExplorerState.run_operation

    @rx.event
    def paginate(self, direction: int):
        if self.busy or not self.collection:
            return
        next_page = self.page + direction
        if next_page < 0 or next_page >= self.pages:
            return
        self.page = next_page
        self._start("records")
        yield ExplorerState.run_operation

    @rx.event
    def page_size(self, data: dict[str, Any]):
        if self.busy or not self.collection:
            return
        value = str(data.get("limit", "25"))
        if value not in {"10", "25", "50", "100"}:
            return
        self.limit = int(value)
        self.page = 0
        self._start("records")
        yield ExplorerState.run_operation

    @rx.event
    def open_record(self, index: int):
        if self.busy or not 0 <= index < len(self._documents):
            return
        self._target = self._documents[index]
        self._target_database = self.database
        self._target_collection = self.collection
        self._start("open")
        yield ExplorerState.run_operation

    @rx.event
    def new_record(self):
        if self.busy or not self.connected or not self.collection:
            return
        self.modal = "add"
        self.editor = "{\n  \n}"
        self.editor_revision += 1
        self.modal_error = ""
        self._target = ""
        self._target_database = self.database
        self._target_collection = self.collection

    @rx.event
    def enable_edit(self):
        if not self.busy and self.modal == "view":
            self.modal = "edit"
            self.editor_revision += 1

    @rx.event
    def confirm_delete(self):
        if not self.busy and self.modal == "view":
            self.modal = "delete"
            self.modal_error = ""

    @rx.event
    def close_modal(self):
        if not self.busy:
            self.modal = ""
            self.editor = ""
            self._target = ""
            self.modal_error = ""

    @rx.event
    def save_record(self, data: dict[str, Any]):
        if self.busy or self.modal not in {"add", "edit"}:
            return
        self.editor = str(data.get("document", ""))
        self._start(self.modal)
        yield ExplorerState.run_operation

    @rx.event
    def delete_record(self):
        if self.busy or self.modal != "delete":
            return
        self._start("delete")
        yield ExplorerState.run_operation

    @rx.event(background=True)
    async def run_operation(self):
        async with self:
            operation = self._operation
            context: dict[str, str | int] = {
                "database": self.database,
                "collection": self.collection,
                "field": self.field,
                "operator": self.operator,
                "value": self.filter_value,
                "page": self.page,
                "limit": self.limit,
                "editor": self.editor,
                "target": self._target,
            }
            invalid_target = operation in {
                "open",
                "add",
                "edit",
                "delete",
            } and (
                self.database != self._target_database
                or self.collection != self._target_collection
            )
        try:
            if invalid_target:
                raise ValueError(
                    "The selected collection changed. Close this dialog and try again."
                )
            result = await asyncio.to_thread(
                perform_operation, operation, context
            )
        except Exception as error:
            logging.exception("Unexpected error")
            connection_failed = isinstance(
                error, (ConnectionFailure, ConfigurationError)
            )
            if connection_failed:
                message = "Unable to connect to MongoDB. Check database network access and TLS settings, then retry."
            elif isinstance(error, DuplicateKeyError):
                message = "A record with that unique key already exists. Review _id and unique fields."
            elif isinstance(error, ValueError):
                message = str(error)
            elif isinstance(error, OperationFailure):
                message = "MongoDB rejected the operation. Check collection permissions and document validation rules."
            else:
                message = "The operation could not be completed. Refresh and try again."
            async with self:
                self.busy = False
                if operation in {"add", "edit", "delete"}:
                    self.modal_error = message
                else:
                    self.error = message
                    self.rows = []
                    self._documents = []
                    self.total = 0
                if connection_failed:
                    self.connection_error = True
                    self.connected = False
            return
        async with self:
            self.busy = False
            self.connection_error = False
            self.connected = True
            if operation == "connect":
                self.databases = result["databases"]
                self.database = result["database"]
                self.collections = result["collections"]
            elif operation == "database":
                self.collections = result["collections"]
            elif operation == "records":
                self.rows = result["rows"]
                self.columns = result["columns"]
                self._documents = result["documents"]
                self.total = result["total"]
                self.page = result["page"]
            elif operation == "open":
                self.editor = result["document"]
                self._target = result["document"]
                self.editor_revision += 1
                self.modal = "view"
            else:
                self.modal = ""
                self._target = ""
                self.editor = ""
                self.success = {
                    "add": "Record added successfully.",
                    "edit": "Record saved successfully.",
                    "delete": "Record deleted successfully.",
                }[operation]
        if operation in {"add", "edit", "delete"}:
            async with self:
                self.busy = True
                self._operation = "records"
            yield ExplorerState.run_operation
