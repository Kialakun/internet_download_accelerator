# idm
--------------------------------
 Internet Download Accelerator
--------------------------------

Created by: Kialakun Galgal
Date: 19/06/2021

Internet download accelerator breaks downloads into byte chunks, and downloads each chunk in a seperate thread. Each thread connects to the resource url, downloads and writes to the download file.

Currently it downloads to the "Downloads" folder of Windows 10.

It has resume capabillities, if a connection is lost. It writes the state of the download to a JSON file and tries to reconnect to the resource.

You can resume from a errored download by entering the url and adding the "--resume 1" flag.

USAGE:
Download repo, create virtual environment (if you want, it doesnt have any dependencies other than Python 3)
Run using cmd.

..> idm [URL] [OPTIONS]

or

..> python idm.py [URL] [OPTIONS]

or

..> python -m idm [URL] [OPTIONS]

OPTIONS: 
    --resume 1 
