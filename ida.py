# import dependencies:
# --------------------
# 'click' is a command line toolkit to create nice CLI
# 'requests' is the http library for humans
# 'threading' is for multi-threading

import click
import requests
import threading
import os.path
import json

# File Info Storge Dict.
FILE_INFO = dict()
DIR = 'C:\\Users\\HP\\downloads\\'
TIMEOUT = 10


# TODO: Complete a way to store downloads to .json file, for easy resuming
def save_download(data, file_name):
    """Save download info to file to be resumed later."""
    with open(f'{file_name}-idm-resume.json', 'w') as f:
        json.dump(data, f)


# start thread with handler
def start_thread(start, end, url_of_file, file_name, i):
    """Start a thread to download file."""
    # print thread info
    print(f'Part {i} - Start: {start}')
    print(f'Part {i} - End: {end}')
    # start thread
    t = threading.Thread(target=Handler,
        kwargs={'start': start, 'end': end, 'url': url_of_file, 'filename': file_name, 'i': i})
    t.setDaemon(True)
    t.start()
 

# re-download a closed connection
def re_download(connections):
    """Re download."""

    for c in connections:
        con = connections[c]
        
        if con['status'] == 'Error':
            print('----------RESTARTING CONNECTION---------------')
            print('CONNECTION: ', c, ' | STATUS: ', con['status'], ' | START: ', con['stopped'], ' | END: ', con['end'])
            print('----------------------------------------------')
            start_thread(start=con['stopped'], end=con['end'], url_of_file=con['url'], file_name=con['file_name'], i=c)


def resume_download_from_file(file_name):
    """Resume download from .json file"""
    # read json file
    f = open(f'{file_name}-idm-resume.json',)
    cons = json.load(f)
    # re download connections
    re_download(cons)

# The below code is used for each chunk of file handled
# by each thread for downloading the content from specified 
# location to storage
def Handler(start, end, url, filename, i): 

    part_size = end - start
    part_size_kb = round(part_size/1000, 2)

    info = {
        i: {
            'start': start,
            'end': end,
            'url': url,
            'file_name': filename
        }
    }
    # set save directory
    save_dir = os.path.join(DIR, filename)
    # set file seeker to start
    seek = start
    var = seek

    # try download and catch any exceptions
    try:
        # set download status
        info[i]['status'] = 'Downloading...'
        # specify the starting and ending of the file
        headers = {'Range': 'bytes=%d-%d' % (start, end)}
        
        r = requests.get(url, headers=headers, stream=True, timeout=TIMEOUT)

        # open the file and write the content of the response
        # into file.
        with open(save_dir, "r+b") as fp:
            # set downloaded chunk size to 0
            downloaded = 0
            # iterate through response content by chunk_size
            # and write to file
            for data in r.iter_content(chunk_size=4096):
                # update downloaded status
                downloaded += round(len(data)/1000, 2)
                # seek to location in file
                fp.seek(seek)
                # write chunk to file at seeked location
                fp.write(data)
                var = fp.tell()
                # move seeker
                seek = seek + len(data)
                # update download info
                # info[i]
                # print download info
                print(f'Connection: {i} | Downloaded: {downloaded} KB 0f {part_size_kb} KB | CurrentPos: {seek}', end='\r')
    
    except requests.exceptions.Timeout:
        print('Request Timeout...')
        # update info
        info[i]['status'] = 'Error'
        info[i]['seek'] = seek
        info[i]['stopped'] = var
        FILE_INFO.update(info) 
        print(info)
        return

    except Exception as e: 
        print(f"An error occured: {e}")
        # update info
        info[i]['status'] = 'Error'
        info[i]['seek'] = seek
        info[i]['stopped'] = var
        # update FILE_INFO
        FILE_INFO.update(info) 
        print(info)
        return

    # update info
    info[i]['status'] = 'Complete'
    info[i]['seek'] = seek
    info[i]['stopped'] = var
    # update FILE_INFO
    FILE_INFO.update(info)
    print(info)
    return


# -- CLI Arguments --
@click.command(help="It downloads the specified file with specified name")
@click.option('--threads',default=8, help="No of Threads")
@click.option('--resume', default=0, help='Resume downloads from file.')
@click.argument('url_of_file', type=click.Path())
@click.pass_context
def download_file(ctx, url_of_file, threads, resume):
    """Download file."""
    # get filename from url
    file_name = url_of_file.split('/')[-1]
    print(f'URL: {url_of_file}')
    print(f'Filename: {file_name}')

    # check if resume
    if resume:
        print("Resuming downloads...")
        resume_download_from_file(file_name)
        join_threads(file_name)
        return

    # get file info from a header request
    r = requests.head(url_of_file, timeout=TIMEOUT)

    try:
        # get file-size
        file_size = int(r.headers['content-length'])
        print(f'File Size: {file_size}')
    except:
        print("Invalid URL")
        return

    # create file with size = file_size
    save_dir = os.path.join(DIR, file_name)
    fp = open(save_dir, "wb")
    fp.write(b'\0' * file_size)
    fp.close()

    # set part size
    part = int(int(file_size) / threads)

    # create threads and pass handler function
    for i in range(threads):
        # set start and end 
        start = part * i
        end = start + part
    
        # create a Thread with start and end locations
        start_thread(start, end, url_of_file, file_name, i)

    # download remainder of file
    if end < file_size:
        i += 1
        start_thread(start=end, end=file_size, url_of_file=url_of_file, file_name=file_name, i=i)

    # end join threads
    join_threads(file_name)


def join_threads(file_name):
    """Join threads."""
    # join threads
    main_thread = threading.current_thread()
    print("Joining threads...")
    for t in threading.enumerate():
        if t is main_thread:
            continue
        t.join()

    print(f'{file_name} downloaded.')
    print('------------SUMMARY--------------')

    for conn in FILE_INFO:
        print( 'CONNECTION ', conn, ': ', FILE_INFO[conn]['status'], ' | SEEK: ', FILE_INFO[conn]['seek'], ' | STOPPED: ', FILE_INFO[conn]['stopped'])
    print('--------------------------------')

    # if any error, save to .json file to be redownloaded
    has_error = False
    for info in FILE_INFO:
        # check if there are any errors
        if FILE_INFO[info]['status'] == 'Error':
            save_download(FILE_INFO, file_name)
            has_error = True
            break

    if has_error:
        # print('Would you like to restart incomplete downloads? (y/n)')
        # ans = input()
        # if ans == 'y':
        # restart download threads
        re_download(FILE_INFO)
        # join threads
        join_threads(file_name)

    print('-------------------COMPLETE----------------')
    for conn in FILE_INFO:
        print( 'CONNECTION ', conn, ': ', FILE_INFO[conn]['status'], ' | SEEK: ', FILE_INFO[conn]['seek'], ' | STOPPED: ', FILE_INFO[conn]['stopped'])
    print('-------------------------------------------')

if __name__ == '__main__':
    try:
        download_file(obj={})
    except KeyboardInterrupt:
        print('Stopping...')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
