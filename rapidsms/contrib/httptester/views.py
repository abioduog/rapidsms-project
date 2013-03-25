#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from random import randint

from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django_tables2 import RequestConfig

from . import forms
from . import storage
from .tables import MessageTable


def generate_identity(request):
    """Simple view to generate a random identity.

    Just generates a random phone number and redirects to the
    message_tester view.

    :param request: HTTP request
    :return: An HTTPResponse
    """
    return redirect("httptester", randint(111111, 999999))


def message_tester(request, identity):
    """The main Message Tester view.

    GET: will display the form, with the default phone number filled
    in from `identity`.

    POST: will process the form and handle it. In this case the identity
    passed to the view is ignored; the identity in the form is used to
    send any messages.

    :param request: HTTP request
    :param identity: Phone number the message will be sent from
    :return: An HTTPResponse
    """
    if request.method == "POST":
        form = forms.MessageForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            identity = cd["identity"]
            if 'clear-all-btn' in request.POST:
                storage.clear_all_messages()
            elif 'clear-btn' in request.POST:
                storage.clear_messages(identity)
            else:
                if "bulk" in request.FILES:
                    for line in request.FILES["bulk"]:
                        line = line.rstrip("\n")
                        storage.store_and_queue(identity, line)
                # no bulk file was submitted, so use the "single message"
                # field. this may be empty, which is fine, since contactcs
                # can (and will) submit empty sms, too.
                else:
                    storage.store_and_queue(identity, cd["text"])
            url = reverse(message_tester, args=[identity])
            return HttpResponseRedirect(url)

    else:
        form = forms.MessageForm({"identity": identity})

    messages_table = MessageTable(storage.get_messages(),
                                  template="httptester/table.html")
    RequestConfig(request, paginate={"per_page": 25}).configure(messages_table)

    context = {
        "router_available": True,
        "message_form": form,
        'messages_table': messages_table,
    }
    return render(request, "httptester/index.html", context)
