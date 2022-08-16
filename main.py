#   pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib


from __future__ import print_function

import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import pandas as pd
import sys
from transformers import pipeline
from transformers import logging
logging.set_verbosity_error()

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# application_path = os.path.dirname(sys.executable)
application_path = '.'

def calculate_avg_happiness_score():
    happiness_csv_path = os.path.join(application_path, 'happiness_scores.csv')
    df = pd.read_csv(happiness_csv_path)
    scores = df['score']
    avg_score = scores.mean()
    # only round to 2 decimal place
    avg_score = round(avg_score, 2)
    return avg_score

def predict_today_score(total_today_notes, task='sentiment'):

    label_score_dict = {'POSITIVE': 10, 'NEGATIVE': 1, 'NEUTRAL': 5}
    if task == 'sentiment':
        classifier = pipeline(task="sentiment-analysis", model='distilbert-base-uncased-finetuned-sst-2-english')
        sentiment = classifier(total_today_notes)
        sentiment = sentiment[0]
        if sentiment['label'] == 'POSITIVE':
            today_score = sentiment['score'] * label_score_dict[sentiment['label']]
        elif sentiment['label'] == 'NEGATIVE':
            today_score = label_score_dict['NEUTRAL'] * (1 - sentiment['score'] * label_score_dict[sentiment['label']])
            if today_score < 1:
                today_score = 1
        else:
            today_score = label_score_dict['NEUTRAL'] * label_score_dict[sentiment['label']]

        print('Your happiness score today: ', today_score)
        return sentiment['label'], sentiment['score'], today_score

    elif task == 'nli':
        classifier = pipeline("text-classification", model='roberta-large-mnli')
        positive_sentence = 'Premise: I had a great day, I feel happy, I am satisfied.\n' + \
                            'Hypothesis: ' + total_today_notes
        negative_sentence = 'Premise: I had a terrible day, bad day, I feel sad, depressed, I am not satisfied.\n' \
                            + 'Hypothesis: ' + total_today_notes
        neutral_sentence = 'Premise: I had normal day, I feel neutral, regular, nothing too exciting.\n' \
                           + 'Hypothesis: ' + total_today_notes
        classifier_pos_result = classifier(positive_sentence)
        classifier_neg_result = classifier(negative_sentence)
        classifier_neu_result = classifier(neutral_sentence)
        results = [classifier_pos_result[0]['score'], classifier_neg_result[0]['score'], classifier_neu_result[0]['score']]
        labels = [classifier_pos_result[0]['label'], classifier_neg_result[0]['label'], classifier_neu_result[0]['label']]
        max_score = max(results)
        max_result = results.index(max_score)
        max_label = labels[max_result]

        # understand sentiment
        # [1, 5]
        if (max_result == 0 and max_label == 'CONTRADICTION') or (max_result == 1 and max_label == 'ENTAILMENT'):
            sentiment = 'NEGATIVE'
            today_score = max(1, label_score_dict['NEUTRAL'] * (1 - max_score))
        # [5, 10]
        elif (max_result == 0 and max_label == 'ENTAILMENT') or (max_result == 1 and max_label == 'CONTRADICTION'):
            sentiment = 'POSITIVE'
            today_score = label_score_dict['NEUTRAL'] * (1 + max_score)

        elif max_result == 0 and max_label == 'NEUTRAL':  # [5, 7.5]
            sentiment = 'NEUTRAL'
            today_score = max(5, 1.5 * label_score_dict['NEUTRAL'] * max_score)
        elif max_result == 1 and max_label == 'NEUTRAL':  # [2.5, 5]
            sentiment = 'NEUTRAL'
            today_score = min(2.5, label_score_dict['NEUTRAL'] * max_score)
        elif max_result == 2:   # [5]
            sentiment = 'NEUTRAL'
            today_score = label_score_dict['NEUTRAL']

        # round to 2 decimal place
        today_score = round(today_score, 2)
        return sentiment, max_score, today_score


def extract_todays_events(service, date_start):
    # Call the Calendar API
    hour_start = datetime.time(0, 0, 1)
    hour_end = datetime.time(23, 59, 59)
    day_start = date_start.isoformat() + 'T' + hour_start.isoformat() + 'Z'  # 'Z' indicates UTC time
    day_end = date_start.isoformat() + 'T' + hour_end.isoformat() + 'Z'
    # now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=day_start,
                                          timeMax=day_end,
                                          # maxResults=10,
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
        return

    # Prints the start and name of the next 10 events
    event_names = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        event_name = event['summary']
        event_names.append(event_name)
        print(start, event_name)

    return event_names


def main_app(user_notes):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of todays events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)
        # ---------- my funcs are from here ----------
        # calender today events
        date_start = datetime.datetime.today().date()
        today_event_names = extract_todays_events(service, date_start)

    except HttpError as error:
        print('An error occurred: %s' % error)

    # ask for user's notes
    # user_notes = input('Please enter your today notes - How was your day?: ')
    # print('Your notes: ', user_notes)

    total_today_notes = 'I think that:' + '\n' + \
                        user_notes + '\n' + \
                        'Today I had the following events:' + \
                        '\n'.join(today_event_names)

    #TODO: remove hebrew chars from total_today_notes
    # TODO: .exe file
    senti_label, senti_score, today_score = predict_today_score(total_today_notes, 'nli')
    # print(senti_label, senti_score)

    week_day = (date_start.toordinal() + 1) % 8 #date_start.weekday()   # Monday = 0
    # save the score and events_names to a csv file
    columns = ['date', 'week_day', 'notes', 'events_names', 'score']
    df = pd.DataFrame({'date': str(date_start),
                       'week_day': week_day,
                       'notes': user_notes,
                       'events_names': [today_event_names],
                       'score': [today_score]})

    happiness_csv_path = os.path.join(application_path, 'happiness_scores.csv')
    if os.path.exists(happiness_csv_path):
        df.to_csv(happiness_csv_path, mode='a', header=False, index=False)
    else:
        df.to_csv(happiness_csv_path, mode='a', index=False, header=True)  # , columns=columns

    return today_score
    # --------------------------------------------




if __name__ == '__main__':
    main_app()