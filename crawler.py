import cookielib
import json
import os.path
import re
import sys
import urllib
import urllib2

class Util:
  """Util to help to generate the URLs and make directory."""

  @staticmethod
  def to_profile_url(profile_id):
    return 'http://www.renren.com/%s' % self.profile_id
  
  @staticmethod
  def to_albumlist_url(profile_id):
    return 'http://photo.renren.com/photo/%s/albumlist/v7' % profile_id

  @staticmethod
  def photo_ajax_query_url(profile_id, album_id, page):
    return 'http://photo.renren.com/photo/%s/album-%s/bypage/ajax/v7?' \
           'page=%d&pageSize=40' % (profile_id, album_id, page)

  @staticmethod
  def create_dir_if_no_exist(directory):
    if not os.path.exists(directory):
      os.makedirs(directory)


class Log:
  """This class is to log the download metric."""

  def __init__(self):
    self.photo_num = 0
    self.album_num = 0

  def start(self):
    print "Start to download photos."

  def photo_increase(self):
    self.photo_num += 1
    if self.photo_num % 50 == 0:
      print 'Already download', self.photo_num, 'photos.'

  def album_increase(self):
    self.album_num += 1

  def summary(self):
    print '***************************************\n' \
          'Download photos successfully:\n'           \
          'Total Photos:', self.photo_num, '\n'       \
          'Total Albums:', self.album_num, '\n'       \
          '***************************************'


class Account:
  """Renren account class for www.renren.com.
  
  This class is responsible for logging, crawling and download all photos to
  local disk.
  """

  def __init__(self, name = '', password = ''):
    self.name = name
    self.password = password
    self.is_login = False
    self.profile_id = ''
    self.cookie_jar = cookielib.LWPCookieJar()
    self.opener = urllib2.build_opener(
      urllib2.HTTPCookieProcessor(self.cookie_jar))
    urllib2.install_opener(self.opener)

  def login(self):
    """Login the account."""
    # Generate the params and request.
    params = {
      'domain': 'www.renren.com',
      'email': self.name,
      'password': self.password}
    request = urllib2.Request(
      'http://www.renren.com/PLogin.do',
      urllib.urlencode(params))

    # Try to login the account.
    try:
      self.openrate = self.opener.open(request)
      url = self.openrate.geturl()
      is_login = re.match('http://www.renren.com/[\d]{9}', url);
      if is_login:
        print 'Login successfuly.'
        self.is_login = True
        self.profile_id = url[-9:]
        return True
      else:
        print 'Account/Password incorrect.'
        return False
    except Exception, e:
      print 'Fail to login.', e.message
      return False;
    return False

  def get_html_content(self, url):
    """Fetch the html content for a given url.
    Args:
      url: The url(string) to crawl the content.
    Returns:
      The html content(string) edcoded in UTF-8.
    """
    request = urllib2.Request(url)
    self.openrate = self.opener.open(request)
    info = self.openrate.read()
    type = sys.getfilesystemencoding()
    return info.decode("UTF-8").encode(type)

  def get_album_ids(self):
    """Get all album id from this accout.
    Returns:
      A list of album ids(string).
    """
    albumlist_url = Util.to_albumlist_url(self.profile_id)
    html_content = self.get_html_content(albumlist_url);
    album_ids = re.findall('\"albumId\":\"[\d]{9}\"', html_content)
    album_ids = map(lambda x: x[-10:-1], album_ids)
    return album_ids 

  def get_photo_urls_in_album(self, album_id):
    """Get all photo urls in the album.
    Args:
      album_id: Alubm id(string) for this accout.
    Returns:
      A list of photo urls(string) in the album.
    """
    photo_urls = []
    for page in range(1, 100):  # max album num
      ajax_url = Util.photo_ajax_query_url(self.profile_id, album_id, page)
      html_content = self.get_html_content(ajax_url)
      data = json.loads(html_content)
      photo_list = data['photoList']
      if len(photo_list) <= 0:
        break
      photo_urls.extend([photo['url'] for photo in photo_list])
    return photo_urls

  def download_photos(self, path):
    """Download all photos from this account to local disk.
    Args:
      path: Local disk path(string).
    """
    log = Log()
    log.start()
    Util.create_dir_if_no_exist(path)
    album_ids = self.get_album_ids();
    for album_id in album_ids:
      photo_urls = self.get_photo_urls_in_album(album_id)
      album_path = path + '/' + str(album_id)
      log.album_increase()
      Util.create_dir_if_no_exist(album_path)
      name = 1
      for photo_url in photo_urls:
        file_path = ''.join([album_path, '/', str(name), '.jpg'])
        urllib.urlretrieve(photo_url, file_path)
        log.photo_increase()
        name += 1
    log.summary()
  
if __name__=='__main__':
  username, password, path = raw_input(), raw_input(), raw_input()
  account = Account(username, password)
  account.login();

  if account.is_login == False:
    sys.exit()

  # Download photos.
  account.download_photos(path)
