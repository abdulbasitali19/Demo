import frappe
from frappe.model.db_query import DatabaseQuery
from frappe.permissions import has_permission
from frappe import _


@frappe.whitelist(allow_guest=True)
def search_in_doctype(doctype, query, limit=10):
    """
    Search within a specified doctype using the Name and Title fields.
    Returns a list of matching records if the user has permission.
    """
    if not doctype or not query:
        return []
    
    user = frappe.session.user
    
    if not frappe.has_permission(doctype, user=user):
        frappe.throw("Not permitted", frappe.PermissionError)
    
    
    meta = frappe.get_meta(doctype)
    title_field = meta.title_field if meta.title_field else "name"
    
    query_filter = f"%{query}%"
    results = frappe.db.sql(f"""
        SELECT name, {title_field} as title
        FROM `tab{doctype}`
        WHERE name LIKE %(query)s OR {title_field} LIKE %(query)s
        LIMIT %(limit)s
    """, {"query": query_filter, "limit": limit}, as_dict=True)
    
    return results

# @frappe.whitelist(allow_guest=True)
# def search_in_doctype(doctype, query, limit=10):
#     """
#     Search within a specified doctype using the Name and Title fields.
#     Returns a list of matching records if the user has permission.
#     """
#     if not doctype or not query:
#         return []

#     user = frappe.session.user


#     if user == "Guest":
#         if not frappe.permissions.has_permission(doctype, "read", user=user) and not frappe.has_permission(doctype, "read"):
#             frappe.throw(f"Guest users are not allowed to access {doctype}", frappe.PermissionError)

   
#     if user != "Guest" and not frappe.has_permission(doctype, "read", user=user):
#         frappe.throw(f"Not permitted to access {doctype}", frappe.PermissionError)

 
#     meta = frappe.get_meta(doctype)
#     title_field = meta.title_field if meta.title_field else "name"

#     query_filter = f"%{query}%"
#     results = frappe.db.sql(f"""
#         SELECT name, {title_field} as title
#         FROM `tab{doctype}`
#         WHERE name LIKE %(query)s OR {title_field} LIKE %(query)s
#         LIMIT %(limit)s
#     """, {"query": query_filter, "limit": limit}, as_dict=True)

#     return results












@frappe.whitelist(allow_guest=False)
def global_search(query):
    if not query:
        return {"message": "Query parameter is required"}
    
    user = frappe.session.user
    results = {}
    
    doctypes = frappe.get_all("DocType", filters={"istable": 0, "issingle": 0}, pluck="name")
    
    for doctype in doctypes:
        if not has_permission(doctype, user=user):
            continue  # Skip unauthorized DocTypes
        
        meta = frappe.get_meta(doctype)
        if "name" in meta.get_valid_columns() or "title" in meta.get_valid_columns():
            search_fields = []
            if "name" in meta.get_valid_columns():
                search_fields.append("name")
            if "title" in meta.get_valid_columns():
                search_fields.append("title")
            
            # Perform search
            conditions = " OR ".join([f"{field} LIKE %s" for field in search_fields])
            values = [f"%{query}%"] * len(search_fields)
            
            search_results = frappe.db.sql(f"""
                SELECT name, {', '.join(search_fields)} FROM `tab{doctype}`
                WHERE {conditions}
                LIMIT 10
            """, values, as_dict=True)
            
            if search_results:
                results[doctype] = search_results
    
    return results if results else {"message": "No results found"}
