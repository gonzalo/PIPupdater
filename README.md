PIPupdater v0.1.5
==========
Alternative to dynamic DNS providers like dnsexit.com, dyndns.org and so. Get your WAN IP address without memberships.

PIPupdater sends you a notification every time your external IP address changes
You can receive this notification through email (SMTP, even Gmail OAuth), 
jabber, Gtalk or Twitter (status update or DM).

http://github.com/gonzalo/PIPupdater

Created and mantained by Gonzalo Cao Cabeza de Vaca Please send any feedback or comments to *gonzalo.cao(at)gmail.com* http://gplus.to/gonzalo.cao

###Features###
* External IP address detection
* Configurable time interval
* Email messaging with SMTP
* IM messaging with any standart XMPP service like Jabber or GTalk
* Twitter support. Post updates to account or send direct messsages
* PIPupdater has been tested with Google and Google Apps accounts

**Coming soon**
* Password encoded config files in order to protect your passwords
* Complete command line support that overrides conf files
* Automatic generation of config files
* Installation as service

###Installation & usage###

Required dependencies: python 2.7, python-oauth2, python-twitter, python-xmpp

In any debian derived distribution (like Ubuntu, Raspbian)just run:

```
$sudo apt-get install python python-oauth2 python-twitter python-xmpp
```
Just create a PIPupdater.conf file and save it in the same folder as 
script, your user home under ~/.PIPupdater/ or /etc/PIPupdater/
Checkout our sample conf file for more details.

```
$ ./PIPupdater.py
usage: PIPupdater.py [-h] [-v] [-m] [-im] [-d]

Use web services to monitorize your WAN IP

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  enable verbose mode (enabled by default if no other output is enabled)
  -m, --mail     send email when IP is updated (requires smtp email account)
  -im, --instant  send IM when IP is updated (requires XMPP/Jabber/Gtalk  account)
  -t, --twitter   send DM tweet when IP is updated (requires register app)
  -d, --debug     enable debug mode (enables verbose mode also)
```
###Changelog###
* 0.1.5 - Twitter support (included DM)
* 0.1.4 - IM with support for Google Apps
* 0.1.3 - IM with XMMP
* 0.1.2 - Mail, Mail using gmail oauth2
* 0.1.1 - IP change detection, verbose mode


###License and disclaimer###
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/.
