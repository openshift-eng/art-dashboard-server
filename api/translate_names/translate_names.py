from api import util


def translate_names_main(name_type, name, name_type2, major=None, minor=None):
    if name_type not in ["distgit", "dist-git"]:
        return {
                   "status": "error",
                   "payload": f"Sorry, don't know how to look up a {name_type} yet."
               }, 400
    if name_type2 not in ["brew-image", "brew-component"]:
        return {
                   "status": "error",
                   "payload": f"Sorry, don't know how to translate to a {name_type2} yet."
               }, 400

    query_name = {
        "brew-image": "image_name",
        "brew-component": "component",
    }[name_type2]
    major_minor = f"{major}.{minor}" if major and minor else "4.5"

    rc, stdout, stderr = util.cmd_gather(
        f"doozer --disable-gssapi --group openshift-{major_minor} --images {name} images:print \'{{{query_name}}}\' --show-base --show-non-release --short")
    if rc:
        return {
                   "status": "error",
                   "payload": f"Sorry, there is no image dist-git {name} in version {major_minor}."
               }, 404
    else:
        return {
                   "status": "success",
                   "payload": {
                       'result': stdout.strip(),
                       'major_minor': major_minor
                   }
               }, 200
