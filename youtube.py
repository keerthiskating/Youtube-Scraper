from googleapiclient.discovery import build
import pprint
import pandas as pd
from googleapiclient.errors import HttpError

pp = pprint.PrettyPrinter(indent=4)


class Youtube:
    def __init__(self, auth_list, input_entity_list):
        self.__developer_key = auth_list['developerkey']
        self.__youtube_api_service_name = auth_list['youtubeapiservicename']
        self.__youtube_api_version = auth_list['youtubeapiversion']
        self.__videoid_list = list()
        self.__youtube_service_obj = None
        self.__input_entity_list = input_entity_list
        self.__comment_df = pd.DataFrame()
        self.__df_list = list()

    def build_service_obj(self):
        self.__youtube_service_obj = build(self.__youtube_api_service_name,
                                           self.__youtube_api_version,
                                           developerKey=self.__developer_key)

    def get_videos(self, keyword, input_list, token):

        search_response = self.__youtube_service_obj.search().list(
            q=keyword,
            type="video",
            pageToken=token,
            part="snippet",
            maxResults=50,
            location=input_list['location'],
            locationRadius=input_list['locationradius']).execute()

        for search_result in search_response.get("items"):
            if search_result["id"]["kind"] == "youtube#video":
                self.__videoid_list.append(search_result['id']['videoId'])
        if 'nextPageToken' in search_response:
            return search_response['nextPageToken'].encode('utf-8')
        else:
            return 'last_page'

    def get_all_videos(self):
        for input_list in self.__input_entity_list:
            for keyword in input_list['keywords']:
                token = None
                while True:
                    if token != 'last_page' or token is None:
                        token = self.get_videos(keyword, input_list, token)
                    else:
                        break
                print('videoid list length: ', len(self.__videoid_list))
                for video_id in self.__videoid_list:
                    self.get_all_comment_threads(video_id, input_list, keyword)
        self.__comment_df = pd.DataFrame(self.__df_list)
        self.__comment_df.to_csv(header=True, path_or_buf='comments.csv')

    def get_all_comment_threads(self, video_id, input_list, keyword):
        next_page_token = None
        while True:
            if next_page_token is None or next_page_token != 'last_page':
                try:
                    next_page_token = self.get_comment_threads(video_id, next_page_token, input_list, keyword)
                except HttpError:
                    pass
            else:
                break

    def get_comment_threads(self, video_id, token, input_list, keyword):

        results = self.__youtube_service_obj.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            textFormat="plainText",
            pageToken=token
        ).execute()

        for item in results["items"]:
            comment = item["snippet"]["topLevelComment"]
            total_reply_count = item["snippet"]["totalReplyCount"]
            author = comment["snippet"]["authorDisplayName"]
            text = comment["snippet"]["textDisplay"].encode('utf-8')
            timestamp = comment["snippet"]["publishedAt"].encode('utf-8')
            temp = {'video_id': video_id,
                    'keyword': keyword,
                    'timestamp': timestamp,
                    'comment': text,
                    'location': input_list['location'],
                    'location_radius': input_list['locationradius'],
                    'type': 'Comment',
                    'source': 'youtube'
                    }
            self.__df_list.append(temp)

            if total_reply_count > 0:

                comment_replies = item["replies"]["comments"]
                for reply in comment_replies:
                    temp.clear()
                    text = reply["snippet"]["textDisplay"].encode('utf-8')
                    timestamp = reply["snippet"]["publishedAt"].encode('utf-8')
                    temp = {'video_id': video_id,
                            'timestamp': timestamp,
                            'comment': text,
                            'location': input_list['location'],
                            'location_radius': input_list['locationradius'],
                            'type': 'Reply to comment',
                            'source': 'youtube'
                            }
                    self.__df_list.append(temp)

        if 'nextPageToken' in results:
            return results['nextPageToken'].encode('utf-8')
        else:
            return 'last_page'

    @staticmethod
    def pretty(d, indent=0):
        for key, value in d.items():
            print('\t' * indent + str(key))
            if isinstance(value, dict):
                Youtube.pretty(value, indent + 1)
            else:
                print('\t' * (indent + 1) + str(value))


auth_list1 = dict(developerkey='REPLACE_WITH_YOUR_KEY',
                  youtubeapiservicename='youtube',
                  youtubeapiversion='v3')

input_list1 = dict(keywords=["Tesla"],
                   location=None,
                   locationradius=None,
                   )
input_list2 = list()
input_list2.append(input_list1)

y = Youtube(auth_list1, input_list2)
y.build_service_obj()
y.get_all_videos()
