# -*- coding: UTF-8 -*-

from behave import step

from dogtail import predicate
from dogtail.tree import root
from common_steps.app import *
from common_steps.appmenu import *
from common_steps.dialogs import *
from dogtail.rawinput import keyCombo, typeText, pressKey, drag


@step(u'Draw a line')
def draw_a_line(context):
    current_window = context.app.get_current_window()
    slide = current_window.child(name='PageShape: Slide 1', roleName='shape')
    (x,y) = slide.position
    (a,b) = slide.size

    drag((x+a/4,y+b/4),(x+a*3/4,y+b*3/4))
