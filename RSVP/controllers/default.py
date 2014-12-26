def index():
    response.flash = T("Welcome to RSVP !")
    events = db(db.events).select()
    for event in events:
        event.count = db((db.attendance.event_id == event.id) & (db.attendance.attending == "yes")).count()
    return dict(events=events)

@auth.requires_login()
def create():
    form = SQLFORM(db.events).process()
    return dict(form=form)

@auth.requires_login()
def edit_event():
    if not request.args:
        redirect(URL('index'))
    eventid = request.args[0]
    event = db(db.events.id == eventid).select().first()
    if not event.created_by == auth.user.id:
        form = "Either the event does not exist or you do not have enough rights to edit this event"
    else:
        form = SQLFORM(db.events, event,showid=False).process()
    return dict(form=form)

@auth.requires_login()
def delete_event():
    if not request.args:
        redirect(URL('index'))
    eventid = request.args[0]
    event = db(db.events.id == eventid).select().first()
    if not event.created_by == auth.user.id:
        session.flash = T("Either the event does not exist or you do not have enough rights to delete this event")
    else:
        db(db.events.id==event.id).delete()
        db(db.attendance.event_id == event.id).delete()
        session.flash = T("Event Deleted successfully")
    redirect(URL('my_events'))

@auth.requires_login()
def my_events():
    events = db(db.events.created_by == auth.user.id).select()
    for event in events:
        event.count = db((db.attendance.event_id == event.id) & (db.attendance.attending == "yes")).count()
    return dict(events=events)

@auth.requires_login()
def events_participated_in():
    events_attending = db((db.attendance.user_id == auth.user.id) & (db.attendance.attending == "yes") & (db.events.from_date >= request.now.date())).select(db.events.ALL, left=db.events.on(db.events.id==db.attendance.event_id))
    for event in events_attending:
        event.count = db((db.attendance.event_id == event.id) & (db.attendance.attending == "yes")).count()
    events_attended = db((db.attendance.user_id == auth.user.id) & (db.attendance.attending == "yes") & (db.events.from_date < request.now.date())).select(db.events.ALL, left=db.events.on(db.events.id==db.attendance.event_id))
    for event in events_attended:
        event.count = db((db.attendance.event_id == event.id) & (db.attendance.attending == "yes")).count()
    return dict(events_attended=events_attended,events_attending=events_attending)

def show():
    if not request.args:
        redirect(URL('index'))
    event = db.events(request.args(0,cast=int))
    event.count = db((db.attendance.event_id == event.id) & (db.attendance.attending == "yes")).count()
    if auth.is_logged_in():
        user.name = "%s %s" % (auth.user.first_name, auth.user.last_name)
        user.altstr = "Changed your mind ?"
        x = db.attendance( (db.attendance.event_id == event.id) & (db.attendance.user_id == auth.user.id) )
        if x:
            if x.attending == "yes":
                user.str = "You are going."
            elif x.attending == "no":
                user.str = "You are not going."
            elif x.attending == "maybe":
                user.str = "You may be going."
            else:
                user.str = "You haven't decided yet."
                user.altstr = "Are you going ?"
        else:
            user.str = "You haven't decided yet."
            user.altstr = "Are you going ?"
    else:
        user.name = ""
        user.str = ""
        user.altstr = ""
    return dict(event=event, user=user)

def action():
    if not request.args:
        redirect(URL('index'))
    eventid = request.args[0]
    userid = request.args[1]
    choice = request.args[2]
    db.attendance.update_or_insert((db.attendance.event_id == eventid) & (db.attendance.user_id == userid), event_id=eventid, user_id=userid, attending=choice)
    db.commit()
    redirect(URL('show',args=[eventid]))

@auth.requires_membership('managers')
def manage_events():
    form = SQLFORM.grid(db.events)
    return dict(form=form)

@auth.requires_membership('managers')
def manage_attendance():
    form = SQLFORM.grid(db.attendance)
    return dict(form=form)

def help():
    return dict()

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())

@auth.requires_login()
@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_login()
def api():
    """
    this is example of API with access control
    WEB2PY provides Hypermedia API (Collection+JSON) Experimental
    """
    from gluon.contrib.hypermedia import Collection
    rules = {
        '<tablename>': {'GET':{},'POST':{},'PUT':{},'DELETE':{}},
        }
    return Collection(db).process(request,response,rules)
