'''
Convenience forms for adding and updating ``Event`` and ``Occurrence``s.

'''
from datetime import datetime, date, time, timedelta

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms.extras.widgets import SelectDateWidget

from dateutil import rrule
from busylissy.blagenda.conf import settings as agenda_settings
from busylissy.blagenda import utils
from busylissy.blagenda.models import *
from busylissy.blproject.models import Project
from busylissy.bltask.models import Task

WEEKDAY_SHORT = (
    (7, _(u'Sun')),
    (1, _(u'Mon')),
    (2, _(u'Tue')),
    (3, _(u'Wed')),
    (4, _(u'Thu')),
    (5, _(u'Fri')),
    (6, _(u'Sat'))
)

WEEKDAY_LONG = (
    (7, _(u'Sunday')),
    (1, _(u'Monday')),
    (2, _(u'Tuesday')),
    (3, _(u'Wednesday')),
    (4, _(u'Thursday')),
    (5, _(u'Friday')),
    (6, _(u'Saturday'))
)

MONTH_LONG = (
    (1,  _(u'January')),
    (2,  _(u'February')),
    (3,  _(u'March')),
    (4,  _(u'April')),
    (5,  _(u'May')),
    (6,  _(u'June')),
    (7,  _(u'July')),
    (8,  _(u'August')),
    (9,  _(u'September')),
    (10, _(u'October')),
    (11, _(u'November')),
    (12, _(u'December')),
)

MONTH_SHORT = (
    (1,  _(u'Jan')),
    (2,  _(u'Feb')),
    (3,  _(u'Mar')),
    (4,  _(u'Apr')),
    (5,  _(u'May')),
    (6,  _(u'Jun')),
    (7,  _(u'Jul')),
    (8,  _(u'Aug')),
    (9,  _(u'Sep')),
    (10, _(u'Oct')),
    (11, _(u'Nov')),
    (12, _(u'Dec')),
)


ORDINAL = (
    (1,  _(u'first')),
    (2,  _(u'second')),
    (3,  _(u'third')),
    (4,  _(u'fourth')),
    (-1, _(u'last'))
)

FREQUENCY_CHOICES = (
    (rrule.DAILY,   _(u'Day(s)')),
    (rrule.WEEKLY,  _(u'Week(s)')),
    (rrule.MONTHLY, _(u'Month(s)')),
    (rrule.YEARLY,  _(u'Year(s)')),
)

REPEAT_CHOICES = (
    ('count', _(u'By count')),
    ('until', _(u'Until date')),
)

ISO_WEEKDAYS_MAP = (
    None,
    rrule.MO,
    rrule.TU,
    rrule.WE,
    rrule.TH,
    rrule.FR,
    rrule.SA,
    rrule.SU
)

MINUTES_INTERVAL = agenda_settings.TIMESLOT_INTERVAL.seconds // 60
SECONDS_INTERVAL = utils.time_delta_total_seconds(agenda_settings.DEFAULT_OCCURRENCE_DURATION)

def timeslot_options(
    interval=agenda_settings.TIMESLOT_INTERVAL,
    start_time=agenda_settings.TIMESLOT_START_TIME,
    end_delta=agenda_settings.TIMESLOT_END_TIME_DURATION,
    fmt=agenda_settings.TIMESLOT_TIME_FORMAT
):
    '''
    Create a list of time slot options for use in agenda forms.
    
    The list is comprised of 2-tuples containing a 24-hour time value and a 
    12-hour temporal representation of that offset.
    
    '''
    dt = datetime.combine(date.today(), time(0))
    dtstart = datetime.combine(dt.date(), start_time)
    dtend = dtstart + end_delta
    options = []

    while dtstart <= dtend:
        options.append((str(dtstart.time()), dtstart.strftime(fmt)))
        dtstart += interval
    
    return options

def timeslot_offset_options(
    interval=agenda_settings.TIMESLOT_INTERVAL,
    start_time=agenda_settings.TIMESLOT_START_TIME,
    end_delta=agenda_settings.TIMESLOT_END_TIME_DURATION,
    fmt=agenda_settings.TIMESLOT_TIME_FORMAT
):
    '''
    Create a list of time slot options for use in agenda forms.
    
    The list is comprised of 2-tuples containing the number of seconds since the
    start of the day and a 12-hour temporal representation of that offset.
    
    '''
    dt = datetime.combine(date.today(), time(0))
    dtstart = datetime.combine(dt.date(), start_time)
    dtend = dtstart + end_delta
    options = []

    delta = utils.time_delta_total_seconds(dtstart - dt)
    seconds = utils.time_delta_total_seconds(interval)
    while dtstart <= dtend:
        options.append((delta, dtstart.strftime(fmt)))
        dtstart += interval
        delta += seconds
    
    return options

default_timeslot_options = timeslot_options()
default_timeslot_offset_options = timeslot_offset_options()


class MultipleIntegerField(forms.MultipleChoiceField):
    '''
    A form field for handling multiple integers.
    
    '''
    def __init__(self, choices, size=None, label=None, widget=None):
        if widget is None:
            widget = forms.SelectMultiple(attrs={'size' : size or len(choices)})
        super(MultipleIntegerField, self).__init__(
            required=False,
            choices=choices,
            label=label,
            widget=widget,
        )

    def clean(self, value):
        return [int(i) for i in super(MultipleIntegerField, self).clean(value)]


class SplitDateTimeWidget(forms.MultiWidget):
    '''
    A Widget that splits datetime input into a SelectDateWidget for dates and
    Select widget for times.
    
    '''
    def __init__(self, attrs=None):
        widgets = (
            SelectDateWidget(attrs=attrs), 
            forms.Select(choices=default_timeslot_options, attrs=attrs)
        )
        super(SplitDateTimeWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.date(), value.time().replace(microsecond=0)]
        
        return [None, None]


class MultipleOccurrenceForm(forms.Form):
    day = forms.DateField(
        label=_(u'Date'),
        initial=date.today,
        widget=SelectDateWidget()
    )
    
    start_time_delta = forms.IntegerField(
        label=_(u'Start time'),
        widget=forms.Select(choices=default_timeslot_offset_options)
    )
    
    end_time_delta = forms.IntegerField(
        label=_(u'End time'),
        widget=forms.Select(choices=default_timeslot_offset_options)
    )

    # recurrence options
    repeats = forms.ChoiceField(
        choices=REPEAT_CHOICES,
        initial='count',
        label=_(u'Occurrences'),
        widget=forms.RadioSelect()
    )

    count = forms.IntegerField(
        label=_(u'Total Occurrences'),
        initial=1,
        required=False,
        widget=forms.TextInput(attrs=dict(size=2, max_length=2))
    )

    until = forms.DateField(
        required=False,
        initial=date.today,
        widget=SelectDateWidget()
    )
    
    freq = forms.IntegerField(
        label=_(u'Frequency'),
        initial=rrule.WEEKLY,
        widget=forms.RadioSelect(choices=FREQUENCY_CHOICES),
    )

    interval = forms.IntegerField(
        required=False,
        initial='1',
        widget=forms.TextInput(attrs=dict(size=3, max_length=3))
    )
    
    # weekly options
    week_days = MultipleIntegerField(
        WEEKDAY_SHORT, 
        label=_(u'Weekly options'),
        widget=forms.CheckboxSelectMultiple
    )
    
    # monthly  options
    month_option = forms.ChoiceField(
        choices=(('on',_(u'On the')), ('each',_(u'Each:'))),
        initial='each',
        widget=forms.RadioSelect(),
        label=_(u'Monthly options')
    )
    
    month_ordinal = forms.IntegerField(widget=forms.Select(choices=ORDINAL))
    month_ordinal_day = forms.IntegerField(widget=forms.Select(choices=WEEKDAY_LONG))
    each_month_day = MultipleIntegerField(
        [(i,i) for i in range(1,32)], 
        widget=forms.CheckboxSelectMultiple
    )
    
    # yearly options
    year_months = MultipleIntegerField(
        MONTH_SHORT, 
        label=_(u'Yearly options'),
        widget=forms.CheckboxSelectMultiple
    )
    
    is_year_month_ordinal = forms.BooleanField(required=False)
    year_month_ordinal = forms.IntegerField(widget=forms.Select(choices=ORDINAL))
    year_month_ordinal_day = forms.IntegerField(widget=forms.Select(choices=WEEKDAY_LONG))
    
    def __init__(self, *args, **kws):
        super(MultipleOccurrenceForm, self).__init__(*args, **kws)
        dtstart = self.initial.get('dtstart', None)
        if dtstart:
            dtstart = dtstart.replace(
                minute=((dtstart.minute // MINUTES_INTERVAL) * MINUTES_INTERVAL),
                second=0, 
                microsecond=0
            )

            weekday = dtstart.isoweekday()
            ordinal = dtstart.day // 7
            ordinal = u'%d' % (-1 if ordinal > 3 else ordinal + 1,)
            
            self.initial.setdefault('week_days', u'%d' % weekday)
            self.initial.setdefault('month_ordinal', ordinal)
            self.initial.setdefault('month_ordinal_day', u'%d' % weekday)
            self.initial.setdefault('each_month_day', [u'%d' % dtstart.day])
            self.initial.setdefault('year_months', [u'%d' % dtstart.month])
            self.initial.setdefault('year_month_ordinal', ordinal)
            self.initial.setdefault('year_month_ordinal_day', u'%d' % weekday)

            offset = (dtstart - datetime.combine(dtstart.date(), time(0))).seconds
            self.initial.setdefault('start_time_delta', u'%d' % offset)
            self.initial.setdefault('end_time_delta', u'%d' % (offset + SECONDS_INTERVAL,))
            

    def clean(self):
        day = datetime.combine(self.cleaned_data['day'], time(0))
        self.cleaned_data['start_time'] = day + timedelta(
            seconds=self.cleaned_data['start_time_delta']
        )
        
        self.cleaned_data['end_time'] = day + timedelta(
            seconds=self.cleaned_data['end_time_delta']
        )

        return self.cleaned_data

    def save(self, event, created=False):
        if self.cleaned_data['repeats'] == 'no':
            params = {}
        else:
            params = self._build_rrule_params()

        if created:
            event.add_occurrences(
                self.cleaned_data['start_time'], 
                self.cleaned_data['end_time'],
                **params
            )
        else:
            occurrence = event.occurrence_set.all()[0]
            occurrence.start_time = self.cleaned_data['start_time']
            occurrence.end_time = self.cleaned_data['end_time']
            occurrence.save()

        return event

    def _build_rrule_params(self):
        iso = ISO_WEEKDAYS_MAP
        data = self.cleaned_data
        params = dict(
            freq=data['freq'],
            interval=data['interval'] or 1
        )
        
        if self.cleaned_data['repeats'] == 'count':
            params['count'] = data['count']
        elif self.cleaned_data['repeats'] == 'until':
            params['until'] = data['until']

        if params['freq'] == rrule.WEEKLY:
            params['byweekday'] = [iso[n] for n in data['week_days']]

        elif params['freq'] == rrule.MONTHLY:
            if 'on' == data['month_option']:
                ordinal = data['month_ordinal']
                day = iso[data['month_ordinal_day']]
                params['byweekday'] = day(ordinal)
            else:
                params['bymonthday'] = data['each_month_day']

        elif params['freq'] == rrule.YEARLY:
            params['bymonth'] = data['year_months']
            if data['is_year_month_ordinal']:
                ordinal = data['year_month_ordinal']
                day = iso[data['year_month_ordinal_day']]
                params['byweekday'] = day(ordinal)
                
        elif params['freq'] != rrule.DAILY:
            raise NotImplementedError(_(u'Unknown interval rule %s') % params['freq'])

        return params

class EventForm(forms.ModelForm):
    '''
    A simple form for adding and updating Event attributes
    
    '''
    class Meta:
        model = Event
        exclude = ('event_type', 'project', 'created_by', 'attending', 'invited', 'content_type', 'object_id')
        
    def __init__(self, project=None, user=None, *args, **kwargs):
        """ If project nog project field """
        super(EventForm, self).__init__(*args, **kwargs)

        if not project:
            self.fields['project'] = forms.ModelChoiceField(label=_('Project'),
                                                            queryset=Project.objects.filter(members=user),
                                                            initial=kwargs['instance'].project.id if 'instance' in kwargs else None,
                                                            empty_label=None)

    def save(self, user, project=None, force_insert=False, force_update=False, commit=True):
        event = super(EventForm, self).save(commit=False)

        event.project = project if project else self.cleaned_data['project']
        event.created_by = user

        if not self.instance.id:
            event.event_type = EventType.objects.get(label='event')

        if event.object:
            event.object.name = self.cleaned_data['title']
            event.object.save()
        
        if commit:
            event.save()
            event.attending.add(user)

        return event

    
class SingleOccurrenceForm(forms.ModelForm):
    '''
    A simple form for adding and updating single Occurrence attributes
    
    '''
    day = forms.CharField(
        label=_(u'Date'),
        initial=date.today,
    )
    
    start_time_delta = forms.IntegerField(
        label=_(u'Start time'),
        widget=forms.Select(choices=default_timeslot_offset_options)
    )
    
    class Meta:
        model = Occurrence
        exclude = ('start_time', 'end_time', )

    def __init__(self, event=None, *args, **kwargs):
        super(SingleOccurrenceForm, self).__init__(*args, **kwargs)

        if hasattr(event, 'object') and event.object is not None:
            self.fields['start_time_delta'].label = ''
            self.fields['start_time_delta'].widget = forms.HiddenInput()

    def clean(self):
        day = datetime.strptime(self.cleaned_data['day'], "%Y-%m-%d")
        self.cleaned_data['start_time'] = day + timedelta(
            seconds=self.cleaned_data['start_time_delta']
        )

        self.cleaned_data['end_time'] = day + timedelta(
            seconds=self.cleaned_data['start_time_delta'] + SECONDS_INTERVAL
        )

        return self.cleaned_data

    def save(self, event, force_insert=False, force_update=False, commit=True):
        occurrence = super(SingleOccurrenceForm, self).save(commit=False)

        occurrence.start_time = self.cleaned_data['start_time']
        occurrence.end_time = self.cleaned_data['end_time']
        occurrence.event = event
        occurrence.save()

        return occurrence
        
        

