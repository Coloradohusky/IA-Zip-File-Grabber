import urllib.request
from urllib.parse import unquote
from bs4 import BeautifulSoup
import subprocess
from argparse import ArgumentParser
import os

startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

def getWebpageData(url):
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0')]
    text = str(opener.open(url).read().decode())
    return text

def getFilesFromZipped(itemId, zipFile):
    url = ('https://archive.org/download/' + itemId + '/' + zipFile + '/').replace(" ", "%20")
    iaDataSoup = BeautifulSoup(getWebpageData(url), 'html.parser')
    filesInZip = []
    for row in iaDataSoup.table:
        if str(type(row)) == "<class 'bs4.element.Tag'>": #navstrings are annoying
            if str(type(row.a)) == "<class 'bs4.element.Tag'>":
                filesInZip.append(str(row.a['href'].replace("//", "https://")))
    return filesInZip

def getZipFiles(itemId):
    zipFiles = subprocess.check_output(['ia', 'list', itemId, '-f', 'TAR',
                                        '-f', 'ZIP', '-f', '7z', '-f', 'RAR'],
                                       shell=False, startupinfo=startupinfo).decode().strip()
    return zipFiles.split("\r\n")

def parse_args():
    parser = ArgumentParser(description="Returns lists of files that are nested inside of 7z, rar, tar, and zip files")
    parser.add_argument("identifier")
    parser.add_argument(
        "--format", help="specify which formats to filter by, separated by comma (ex. --format mkv,mp4,jpg)"
        )
    parser.add_argument(
        "--download", action="store_true", help="downloads grabbed URLs with WGET"
        )
    args = parser.parse_args()
    return args

def downloadFiles(itemId, itemList):
    if not os.path.exists(itemId):
        os.mkdir(itemId)
    os.chdir(itemId)
    for i in itemList:
        a = unquote(i[0].split('/')[-2])
        if not os.path.exists(a):
            os.mkdir(a)
        os.chdir(a)
        for j in i:
            print (j)
            filename = unquote(unquote(j.split('/')[-1])).replace('/', '_')
            subprocess.check_output(['curl', j, '-L', '--output', filename], shell=False, startupinfo=startupinfo)
            j = unquote(j)
            print (unquote(a + '/' + j.split('/')[-1] + ' downloaded.'))
            print ()
        os.chdir('..')
    os.chdir('..')
        

def main():
    args = parse_args()
    itemId = args.identifier
    download = args.download
    filters = str(args.format).split(',')
    try:
        zipFiles = getZipFiles(itemId)
    except subprocess.CalledProcessError:
        print ('No zip files found for ' + itemId)
        return False
    totalFilesInZip = []
    for zipFile in zipFiles:
        filesInZip = getFilesFromZipped(itemId, zipFile)
        filteredFiles = []
        if str(filters[0]) == "None":
            filteredFiles = filesInZip
        else:
            for file in filesInZip:
                if file.endswith(tuple(filters)):
                    filteredFiles.append(file)
        totalFilesInZip.append(filteredFiles)
    if not any(totalFilesInZip):
        print ('None of your selected formats were found in ' + itemId)
        return False
    print (totalFilesInZip)
    if download:
        downloadFiles(itemId, totalFilesInZip)

if __name__ == "__main__":
    main()
