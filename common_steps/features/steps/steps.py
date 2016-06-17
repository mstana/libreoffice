# -*- coding: UTF-8 -*-
from behave import step, when, then

import subprocess
import os


@step('no abrt alerts found')
def no_abrt_alerts(context):
    if not os.path.exists("/usr/bin/abrt-cli"):
        context.scenario.skip("No abrt-cli found")
        return

    try:
        command = "abrt-cli list"
        print("Running '%s'" % command)
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        output = process.communicate()[0].rstrip()
    finally:
        print(output)

    assert output == ''


@step('no selinux alerts found')
def no_selinux_alerts(context):
    if not os.path.exists("/usr/bin/sealert"):
        print("No sealert found")
        context.scenario.skip()
        return

    try:
        command = "sealert -l '*'"
        print("Running '%s'" % command)
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        output = process.communicate()[0].rstrip()
    finally:
        print(output)

    assert output == ''


@step('rpmlint produces no errors')
def no_rpmlint_errors(context):
    if not os.path.exists("/usr/bin/rpmlint"):
        context.scenario.skip("No rpmlint found")
        return

    get_package_name(context)
    if not context.pkg_name:
        context.scenario.skip("Can't find package for tests")
        return

    try:
        print("Running 'rpmlint %s" % context.pkg_name)
        process = subprocess.Popen("rpmlint %s*.rpm" % context.pkg_name, shell=True, stdout=subprocess.PIPE)
        output = process.communicate()[0].rstrip()
    finally:
        print(output)

    errors_num = output.split('\n')[-1].split(';')[-1].split(',')[0].strip().split(' ')[0]
    if errors_num != '0':
        # Skip annoying incorrect-fsf-address
        if not (errors_num == '1' and 'E: incorrect-fsf-address' in output):
            raise Exception("rpmlint errors found")


def get_package_name(context):
    pkg_name = None
    # Use app command
    # Read setting passed via cli (available since 1.2.5)
    if hasattr(context.config, 'userdata') and 'package' in context.config.userdata:
        pkg_name = context.config.userdata['package']
    elif hasattr(context, 'app') and hasattr(context.app, 'appCommand'):
        pkg_name = context.app.appCommand

    if not pkg_name:
        return False

    context.pkg_name = pkg_name

    # Get a list of files in the package
    process = subprocess.Popen("rpm -ql %s" % pkg_name, shell=True, stdout=subprocess.PIPE)
    files_list_output = process.communicate()[0]
    if not files_list_output:
        raise Exception("Files list is empty")
    files_list = files_list_output.strip().split('\n')

    # Sort files and detect bins, configs and mans
    context.man_check_binaries = []
    context.man_check_configs = []
    context.man_check_man_pages = []
    for file_name in files_list:
        for bin_path in ["/bin", "/sbin", "/usr/bin", "/usr/sbin"]:
            if file_name.startswith(bin_path):
                context.man_check_binaries.append(file_name)
        if file_name.startswith("/etc") and not file_name.startswith("/etc/xdg"):
            context.man_check_configs.append(file_name)
        if file_name.startswith("/usr/share/man"):
            context.man_check_man_pages.append(file_name)

    return True


def get_man_page_for_file(context, file_name):
    for man_page in context.man_check_man_pages:
        man_page_file = man_page.split('/')[-1]
        expected_name = '.'.join(man_page_file.split('.')[:-2])
        if expected_name == file_name.split('/')[-1]:
            return man_page

    return None


@when(u'package has man pages')
def package_has_man_pages(context):
    # Store package name in context.pkg_name
    if not get_package_name(context):
        context.scenario.skip("Can't find package for tests")
        return


@then(u'all binary files from this package have a man page')
def bin_files_have_man_page(context):
    for bin_path in context.man_check_binaries:
        if not get_man_page_for_file(context, bin_path):
            raise Exception("Can't find man page for '%s' in '%s'" % (bin_path, context.man_check_man_pages))


@then(u'all config files from this package have a man page')
def conf_files_have_man_page(context):
    for conf_path in context.man_check_configs:
        if not get_man_page_for_file(context, conf_path):
            raise Exception("Can't find man page for '%s' in '%s'" % (conf_path, context.man_check_man_pages))


@then(u'no unused man page files are supplied')
def no_unused_man_pages_exist(context):
    binaries_and_confs_files = context.man_check_binaries + context.man_check_configs
    binaries_and_confs_mans = []
    for file_path in binaries_and_confs_files:
        binaries_and_confs_mans.append(get_man_page_for_file(context, file_path))

    if set(binaries_and_confs_mans) != set(context.man_check_man_pages):
        raise Exception("Unused mans found, expected:\n%s\n but was:\n%s" % (
            binaries_and_confs_mans, context.man_check_man_pages))


@then(u'binaries are placed in section 1 or 8')
def binaries_are_in_section_1_or_8(context):
    for bin_path in context.man_check_binaries:
        man_page = get_man_page_for_file(context, bin_path)
        if not man_page:
            raise Exception("Can't find man page for '%s' in '%s'" % (bin_path, context.man_check_man_pages))
        else:
            section = man_page.split('.')[-2]
            if section not in ["1", "8"]:
                raise Exception("Expected '%s' to be in section 1 or 8" % man_page)


@then(u'configs are placed in section 5')
def configs_are_in_section_5(context):
    for conf_path in context.man_check_configs:
        man_page = get_man_page_for_file(context, conf_path)
        if not man_page:
            raise Exception("Can't find man page for '%s' in '%s'" % (conf_path, context.man_check_man_pages))
        else:
            section = man_page.split('.')[-1]
            if section != "5":
                raise Exception("Expected '%s' to be in section 5" % man_page)


@then(u'lexgrog for each man page parsing passes')
def lexgrog_parsing(context):
    if not os.path.exists("/usr/bin/lexgrog"):
        context.scenario.skip("lexgrog not found")
        return

    binaries_and_confs_files = context.man_check_binaries + context.man_check_configs
    for file_path in binaries_and_confs_files:
        subprocess.Popen("lexgrog %s" % file_path, shell=True, stdout=subprocess.PIPE)
