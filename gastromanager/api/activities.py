# LOGIC FOR REGISTERING FUNCTIONALITIES IN THE JOURNAL USING THE @register_activity DECORATOR

# To register a view, configure it here with an initial action set to None.
# Then, return the action with the activity message to be displayed in the journal.

# If the registration is related to information being deleted from the database,
# configure it directly in the view.py.


def activity_staff_view(request, *args, **kwargs):
    action = None  # Start with None (if not it registers everything)
    username = ""

    if "add_user" in request.POST:
        username = request.POST.get("username")
        action = f"User created: {username}"
    elif "delete_user" in request.POST:
        return None

    return action


def activity_edit_profile(request, *args, **kwargs):
    action = None

    if request.method == "POST":
        username = request.POST.get("username")
        action = f"User updated: {username}"

    return action


def scan_journal_log(request, *args, **kwargs):
    action = None

    if request.method == "POST":
        username = request.POST.get("username")
        action = f"User updated: {username}"

    return action
