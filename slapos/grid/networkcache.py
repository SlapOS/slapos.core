##############################################################################
#
# Copyright (c) 2010, 2011, 2012 ViFiB SARL and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
from __future__ import print_function

import ast
import json
import shutil
import subprocess
import traceback

from slapos.grid.distribution import os_matches, distribution_tuple

try:
    try:
        from slapos.libnetworkcache import NetworkcacheClient, UploadError, \
          DirectoryNotFound
    except ImportError:
        LIBNETWORKCACHE_ENABLED = False
    else:
        LIBNETWORKCACHE_ENABLED = True
except Exception:
    print('There was problem while trying to import slapos.libnetworkcache:\n%s'
          % traceback.format_exc())
    LIBNETWORKCACHE_ENABLED = False
    print('Networkcache forced to be disabled.')



def fallback_call(function):
    """Decorator which disallow to have any problem while calling method"""
    def wrapper(self, *args, **kwd):
        """
        Log the call, and the result of the call
        """
        try:
            return function(self, *args, **kwd)
        except Exception:
            print('There was problem while calling method %r:\n%s' % (
                function.__name__, traceback.format_exc()))
            return False
    wrapper.__doc__ = function.__doc__
    return wrapper


def multiarch():
    return subprocess.check_output(
        ('gcc', '-dumpmachine'), universal_newlines=True,).rstrip()


def machine_info_tuple():
    return multiarch(), distribution_tuple()


def is_compatible(machine_info_tuple, required_info_tuple):
    return machine_info_tuple[0] == required_info_tuple[0] \
        and os_matches(required_info_tuple[1], machine_info_tuple[1])


def loadJsonEntry(jentry):
    entry = json.loads(jentry)
    if 'multiarch' not in entry and entry['machine'] == 'x86_64': # BBB
        entry['multiarch'] = 'x86_64-linux-gnu'
        entry['os'] = list(ast.literal_eval(entry['os']))
    return entry


def download_entry_list(cache_url, dir_url, key, logger,
                        signature_certificate_list):
    nc = NetworkcacheClient(cache_url, dir_url,
        signature_certificate_list=signature_certificate_list or None)
    entry_list = nc.select_generic(key, filter=False)
    return [(entry[0], nc.verifySignatureInCertificateList(*entry))
            for entry in entry_list]


@fallback_call
def download_network_cached(cache_url, dir_url, software_url, software_root,
                            key, path, logger, signature_certificate_list,
                            download_from_binary_cache_url_blacklist=None):
    """Downloads from a network cache provider

    return True if download succeeded.
    """
    if not LIBNETWORKCACHE_ENABLED:
        return False

    if not(cache_url and dir_url and software_url and software_root):
        return False

    for url in download_from_binary_cache_url_blacklist:
      if software_url.startswith(url):
        return False

    try:
        nc = NetworkcacheClient(cache_url, dir_url,
            signature_certificate_list=signature_certificate_list or None)
    except TypeError:
      logger.warning('Incompatible version of networkcache, not using it.')
      return False

    logger.info('Downloading %s binary from network cache.', software_url)
    try:
        file_descriptor = None
        machine_info = machine_info_tuple()
        for entry, _ in nc.select_generic(key):
            try:
                tags = loadJsonEntry(entry)
                if is_compatible(machine_info, (tags['multiarch'], tags['os'])):
                    file_descriptor = nc.download(tags['sha512'])
                    break
            except Exception:
                pass
        if file_descriptor is not None:
            f = open(path, 'w+b')
            try:
                shutil.copyfileobj(file_descriptor, f)
            finally:
                f.close()
                file_descriptor.close()
            return True
    except (IOError, DirectoryNotFound) as e:
        logger.info(
          'Failed to download from network cache %s: %s', software_url, e)
    return False


@fallback_call
def upload_network_cached(software_root, software_url, cached_key,
    cache_url, dir_url, path, logger, signature_private_key_file,
    signature_certificate_list, shacache_ca_file, shacache_cert_file,
    shacache_key_file, shadir_ca_file, shadir_cert_file, shadir_key_file):
    """Upload file to a network cache server"""
    if not LIBNETWORKCACHE_ENABLED:
        return False

    if not (software_root and software_url and cached_key \
                          and cache_url and dir_url):
        return False

    logger.info('Uploading %s binary into network cache.', software_url)

    # YXU: "file" and "urlmd5" should be removed when server side is ready
    kw = dict(
      file="file",
      urlmd5="urlmd5",
      software_url=software_url,
      software_root=software_root,
      multiarch=multiarch(),
      os=distribution_tuple(),
    )

    f = open(path, 'rb')
    # convert '' into None in order to call nc nicely
    if not signature_private_key_file:
        signature_private_key_file = None
    if not shacache_ca_file:
        shacache_ca_file = None
    if not shacache_cert_file:
        shacache_cert_file = None
    if not shacache_key_file:
        shacache_key_file = None
    if not shadir_ca_file:
        shadir_ca_file = None
    if not shadir_cert_file:
        shadir_cert_file = None
    if not shadir_key_file:
        shadir_key_file = None
    try:
        nc = NetworkcacheClient(cache_url, dir_url,
            signature_private_key_file=signature_private_key_file,
            signature_certificate_list=signature_certificate_list,
            shacache_ca_file=shacache_ca_file,
            shacache_cert_file=shacache_cert_file,
            shacache_key_file=shacache_key_file,
            shadir_ca_file=shadir_ca_file,
            shadir_cert_file=shadir_cert_file,
            shadir_key_file=shadir_key_file)
    except TypeError:
        logger.warning('Incompatible version of networkcache, not using it.')
        return False

    try:
        return nc.upload_generic(f, cached_key, **kw)
    except (IOError, UploadError) as e:
        logger.info('Failed to upload file. %s', e)
        return False
    finally:
      f.close()

    return True
