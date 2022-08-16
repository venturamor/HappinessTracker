from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

import random
import os
import sys

from main import main_app, calculate_avg_happiness_score
from config import config

# application_path = os.path.dirname(sys.executable)
application_path = '.'

def random_image():
    images_path = os.path.join(application_path, 'images')
    return os.path.join(images_path, random.choice(os.listdir(images_path)))


def get_motivation_quote():
    # random line from motivation.txt
    motivation_path = os.path.join(os.path.join(application_path, 'motivational_texts'), 'motivation_text.txt')
    with open(motivation_path, 'r', encoding='utf') as f:
        lines = f.readlines()
        return random.choice(lines)


class GratitudeCalender(App):
    def build(self):
        #returns a window object with all it's widgets
        self.window = GridLayout()
        self.window.cols = 1
        self.window.size_hint = (0.6, 0.7)
        self.window.pos_hint = {"center_x": 0.5, "center_y":0.5}

        greeting_name_text = "Hello {}!\n".format(config['user_name'])
        self.greeting_name = Label(text=greeting_name_text, font_size=40)
        self.window.add_widget(self.greeting_name)
        # image widget
        image_path = random_image()
        self.window.add_widget(Image(source=image_path,
                                     size_hint=(4, 4)))

        # label widget
        self.greeting_day = Label(
                        text="How was your day?",
                        font_size=14,
                        color='#00FFCE'
                        )
        self.window.add_widget(self.greeting_day)

        # text input widget
        self.user = TextInput(
                    multiline=False,
                    padding_y=(20, 20),
                    size_hint=(2, 2)
                    )

        self.window.add_widget(self.user)

        # button widget
        self.button = Button(
                      text="Predict My Daily Happiness Score & Save",
                      size_hint=(1, 0.5),
                      bold=True,
                      background_color='#006994', #'#00FFCE',
                      #remove darker overlay of background colour
                      background_normal = ""
                      )
        self.button.bind(on_press=self.callback_predict_score)
        self.window.add_widget(self.button)

        # motivation label
        motivation_qoute = get_motivation_quote()
        self.motivation_label = Label(
                            text=motivation_qoute,
                            font_size=12,
                            color='#FFCC00' #'#00FFCE'
                            )

        # avg score by now button
        self.avg_score_button = Button(
                            text="Average Score By Now",
                            size_hint=(1, 0.5),
                            bold=True,
                            background_color='#00FFCE',
                            #remove darker overlay of background colour
                            # background_normal = ""
                            )
        self.avg_score_button.bind(on_press=self.callback_calc_avg)
        self.window.add_widget(self.avg_score_button)


        # copy rights label
        self.copy_right = Label(text="Copyright © 2022 Mor·Ventura",
                                font_size=10)

        self.window.add_widget(self.copy_right)

        return self.window

    def callback_predict_score(self, instance):
        # change label text to "Hello + user name!"
        today_score = main_app(self.user.text)
        self.greeting_day.text = "\nToday score: {}.\n".format(today_score)
        self.window.add_widget(self.motivation_label)

    def callback_calc_avg(self, instance):
        avg = calculate_avg_happiness_score()
        self.avg_score_button.text = "\nAverage Score By Now: {}.\n".format(avg)


# run GratitudeCalender App Class
if __name__ == "__main__":
    GratitudeCalender().run()