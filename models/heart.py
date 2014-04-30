from google.appengine.ext import db
from datetime import datetime, timedelta
from models import resuscitate_mail, flatline_mail
from lib.croniter import croniter
from pytz.gae import pytz


class Heart(db.Model):
    title = db.StringProperty(default='')
    created = db.DateTimeProperty(auto_now_add=True)
    last_pulse = db.DateTimeProperty(auto_now_add=True)
    threshold = db.IntegerProperty(default=0)
    cron = db.StringProperty(default='')
    time_zone = db.StringProperty(default='UTC')
    maintenance_day = db.DateProperty(default=None)

    def registerPulse(self):
        flatline = self.getActiveFlatline()
        if flatline is not None:
            flatline.resuscitate()
        self.last_pulse = datetime.now()
        self.put()

    def getActiveFlatline(self):
        return Flatline.all().ancestor(self.key()).filter("active =", True).get()

    def checkFlatLine(self):
        if self.threshold == 0 or self.cron == '':
            return

        active = self.getActiveFlatline()
        if active is not None:
            return

        if not self.is_flatlined():
            return
        f = Flatline(parent=self)
        f.start = self.last_pulse
        f.put()
        flatline_mail(self)

    def is_flatlined(self):
        if self.cron == '':
            return self.last_pulse + timedelta(seconds=self.threshold*2) < datetime.utcnow()

        if self.time_zone is None:
            self.time_zone = 'UTC'

        local_time_zone = pytz.timezone(self.time_zone)

        # return false if today is maintenance day
        if self.maintenance_day is not None and self.maintenance_day.strftime('%Y-%m-%d') == local_time_zone.localize(datetime.utcnow()).strftime('%Y-%m-%d'):
            return False

        offset = timedelta(seconds=self.threshold)

        last_pulse_local = pytz.utc.localize(self.last_pulse).astimezone(local_time_zone)
        next_date = croniter(self.cron, last_pulse_local).get_next(datetime)
        next_date = local_time_zone.localize(next_date)
        next_next_date = croniter(self.cron, next_date).get_next(datetime)
        next_date = next_date.astimezone(pytz.utc)
        next_next_date = local_time_zone.localize(next_next_date).astimezone(pytz.utc)
        now = pytz.utc.localize(datetime.now())

        # flatline if next_date and last_pulse are outside offset 
        if abs((next_date - last_pulse_local).total_seconds()) < self.threshold:
            return next_next_date + offset < now

        return  next_date + offset < now

    def check_maintenance(self):
        # Clear active flatline if today is maintenance day
        if datetime.today().date() != self.maintenance_day:
            return
        dayAfterMaintenanceDay = datetime.combine(datetime.today().date() + timedelta(days=1), datetime.min.time())
        self.last_pulse = dayAfterMaintenanceDay
        active_flatline = self.getActiveFlatline()
        if active_flatline is None:
            return
        active_flatline.close()
        active_flatline.put()

    def get_last_closed_by(self):
        last_flatline = Flatline.all().ancestor(self.key()).order("-end").get()
        if last_flatline is None:
            return
        return last_flatline.closed_reason 

class Flatline(db.Model):
    start = db.DateTimeProperty(auto_now_add=True)
    active = db.BooleanProperty(default=True)
    end = db.DateTimeProperty()
    closed_reason = db.StringProperty(default='')

    def resuscitate(self):
        self.active = False
        self.end = datetime.now()
        self.closed_reason = "Pulse received"
        resuscitate_mail(self.parent())

        self.put()

    def close(self):
        self.active = False
        self.end = datetime.now()
        self.closed_reason = "Maintenance"

        self.put()
