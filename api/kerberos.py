import subprocess
import os


def do_kinit():
    """
    Function performs kinit with the already mounted keytab
    :return: None
    """
    if "KERBEROS_KEYTAB" in os.environ:
        keytab_file = os.environ["KERBEROS_KEYTAB"]
        principal = os.environ["KERBEROS_PRINCIPAL"]
        kinit_request = subprocess.Popen(["kinit", "-kt", keytab_file, principal],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = kinit_request.communicate()
        if error:
            print(f"Kerberos error: {error}")
