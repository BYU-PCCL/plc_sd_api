import os
import requests

headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f'Basic {os.environ["DID_API_TOKEN"]}'
    }

def get_talks():
    url = 'https://api.d-id.com/talks?limit=100'

    response = requests.get(url=url, headers=headers)

    talks = response.json()["talks"]

    return talks


def get_first_video_file():

    talks = get_talks()

    video_file = requests.get(talks[0]["result_url"])

    bytes = video_file.content

    print(bytes)


def delete_all_talks():
    for each_talk in get_talks():
        url = f"https://api.d-id.com/talks/{each_talk['id']}"

        requests.delete(url=url, headers=headers)



if __name__ == "__main__":
    talks = get_talks()
    print(talks)
    print(len(talks))
