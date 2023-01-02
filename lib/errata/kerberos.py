import subprocess

KEYTAB_FILE_PATH = "/tmp/keytab/redhat.keytab"


def handle_kinit():
    """
    Funtion performs kinit
    :return: None
    """
    kinit_request = subprocess.Popen(["kinit", "-kt", KEYTAB_FILE_PATH, "ocp-readonly/psi.redhat.com@REDHAT.COM"],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = kinit_request.communicate()
    if error:
        print(error)
