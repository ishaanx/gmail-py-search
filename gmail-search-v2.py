from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
from datetime import datetime
import csv
import sys


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
f = open("data.csv", 'wt', buffering=1000, encoding='utf-8')
f.write("Timestamp,Property,Reservation Type,Confirmation" + '\n')
def main():

    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    query=sys.argv[1]
    print(query)
    
    response = service.users().messages().list(userId='me', q=query).execute()

    if 'messages' in response:
        process_messages(service, response['messages'])

    while 'nextPageToken' in response:
        page_token = response['nextPageToken']
        response = service.users().messages().list(userId='me', q=query,
                                                   pageToken=page_token).execute()
        process_messages(service, response['messages'])
    f.close()


def process_messages(service,messages):
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()

        try:
            if 'parts' in msg['payload']:
                base_string = msg['payload']['parts'][0]['body']['data']
            else:
                base_string = msg['payload']['body']['data']
            if not base_string.endswith('=='):
                base_string = base_string + '=='
               
            payload = base64.b64decode(base_string)
            payload = payload.decode("UTF-8")
            if payload.startswith('{"code-type-suffix":"'):
                subbody = payload.replace('{"code-type-suffix":"', '')
                subbody = subbody.split('"', 2)
                internal_date = msg['internalDate']
                dt = datetime.fromtimestamp(int(internal_date) / 1000)
                f.write(dt.strftime('%Y-%m-%d-%H:%M')+','+subbody[0].replace("-", ","))
                f.write('\n')
                print(dt.strftime('%Y-%m-%d-%H:%M')+','+subbody[0].replace("-", ","))

        except Exception as err:
            print(err)


if __name__ == '__main__':
    main()
