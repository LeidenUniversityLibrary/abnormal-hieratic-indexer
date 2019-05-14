# Abnormal Hieratic Indexer

Script that indexes annotations in the Abnormal Hieratic Global Portal. This script is specifically
tailored towards the annotations created for the AHGP.

Annotations in the AHGP are stored in a [Simple Annotation Server][sas], but for search we use [Elasticsearch][es].

[sas]: https://github.com/glenrobson/SimpleAnnotationServer
[es]: https://www.elastic.co/guide/en/elasticsearch/

## Installation

This script was developed with Python 3.6+. It may run on other versions, but this is not tested.

The indexer depends on [requests][] and [beautifulsoup4][], both of which may be installed with `pip` or `pip3` (depending on your system).
On some Linux distributions they may instead be available as packages for your package manager.

```
pip install requests beautifulsoup4
```

[requests]: https://2.python-requests.org//en/master/
[beautifulsoup4]: https://www.crummy.com/software/BeautifulSoup/

## Usage

Currently all information needed to run is defined within the script.
This includes the endpoint of the ElasticSearch server and
the base URL of the SimpleAnnotationServer endpoint.
If you need to adjust these settings, modify the script.

To enable periodic indexing, you can set up a cronjob or Systemd timer.

### cronjob

This is an example cronjob that uses the Red Hat software collection for Python 3.6 and saves standard out and standard error streams to files. (Note that cronjobs need to escape the `%` in file names, whereas in shell scripts the extra backslashes do not work.)

```
33 8,12,16,20 * * * scl enable rh-python36 'python /home/beheer/index_annotations.py' > "/var/log/anno-index/indexing_$(date '+\%Y\%m\%d\%H\%M').log" 2> "/var/log/anno-index/error_$(date '+\%Y\%m\%d\%H\%M').log"
```

# Author and license

Abnormal Hieratic Indexer has been created by Ben Companjen at the Centre for Digital Scholarship.

© 2019 Leiden University Libraries

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
