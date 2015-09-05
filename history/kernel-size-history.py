#!/usr/bin/python3

import sys, os, re, argparse, requests, tarfile, subprocess, shlex, shutil, glob

class defaults:
    versions = ["3.0", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8",
                "3.9", "3.10", "3.11", "3.12", "3.13", "3.14", "3.15", "3.16",
                "3.17", "3.18", "3.19", "4.0", "4.1"]
    sourceMirror="https://www.kernel.org/pub/linux/kernel"
    class dir:
        download="dl"
        build="build_dir"
        bin="bin"

def mirrorDir(version):
    v = version.split(".")
    if v[0] is "2":
        return "v" + v[0] + "." + v[1]
    else:
        return "v" + version.split(".")[0] + ".x"

def showProgress(prefix, size, total):
    sys.stdout.write("%s%1.3f MB (%1.1f %%)\r" %
                     (prefix,
                      size / 1024.0 / 1024.0,
                      100.0 * size / total))
    
def wget(url, progress=True, progressPrefix=None, out="."):
    if os.path.isdir(out):
        filepath = os.path.join(out, os.path.basename(url))
    else:
        filepath = out
    r = requests.get(url, stream=True)
    chunkSize=1024
    total = int(r.headers['content-length'])
    size = 0
    with open(filepath, 'wb') as f:
        for chunk in r.iter_content(chunk_size=chunkSize):
            f.write(chunk)
            size += chunkSize
            if progress:
                showProgress(progressPrefix, size, total)
    if progress:
        print()
    if r.status_code != requests.codes.ok:
        os.unlink(filepath)
        r.raise_for_status()
    return filepath

def archiveBase(version):
    return 'linux-' + version

def kernelArchive(version):
    return archiveBase(version) + '.tar.xz'

def fetchKernelSource(args, version):
    if not os.path.exists(args.dl_dir):
        os.makedirs(args.dl_dir)
    url = args.src_mirror + '/' + mirrorDir(version) + '/' + kernelArchive(version)
    wget(url, progressPrefix="Fetch " + url + " to " + args.dl_dir + ": ", out=args.dl_dir)

def extractKernelSource(args, version):
    tarfilepath = os.path.join(args.dl_dir, kernelArchive(version))
    if not os.path.isfile(tarfilepath):
        sys.exit("error: missing source archive: " + tarfilepath + ". Did you forget --fetch-sources?")
    if not os.path.exists(args.build_dir):
        os.makedirs(args.build_dir)
    print("Extract " + tarfilepath + " to " + args.build_dir)
    with tarfile.open(tarfilepath, mode="r") as f:
        f.extractall(args.build_dir)

def deleteKernelSource(args, version):
    build_dir = os.path.join(args.build_dir, archiveBase(version))
    print("Deleting " + build_dir)
    shutil.rmtree(build_dir)
    
def buildKernelImages(args, version):
    if not os.path.exists(args.bin_dir):
        os.makedirs(args.bin_dir)
    bin_dir_arch = os.path.join(args.bin_dir, args.arch)
    if not os.path.exists(bin_dir_arch):
        os.makedirs(bin_dir_arch)
    bin_dir = os.path.join(bin_dir_arch, archiveBase(version))
    build_dir = os.path.join(args.build_dir, archiveBase(version))
    make = ["make",  args.make_args, "ARCH=" + args.arch ]
    makeConfig = make + [ args.kernel_defconfig ] 
    if not os.path.isdir(build_dir):
        sys.exit("error: missing build directory: " + build_dir + ". Did you forget --extract-sources?")
    print("Configure " + version + " in " + build_dir + ": " + " ".join(shlex.quote(s) for s in makeConfig))
    with subprocess.Popen(makeConfig, cwd=build_dir) as p:
        p.wait()
        if p.returncode:
            sys.exit("error: failed configuring kernel for build")
    print("Build " + version + " in " + build_dir + ": " + " ".join(shlex.quote(s) for s in make))
    with subprocess.Popen(make, cwd=build_dir) as p:
        p.wait()
        if p.returncode:
            sys.exit("error: failed building kernel for build")
    if not os.path.exists(bin_dir):
        os.makedirs(bin_dir)
    images = [ os.path.join(build_dir, "vmlinux") ]
    images += glob.glob(os.path.join(build_dir, "arch", args.arch, "boot", "*Image"))
    for image in images:
        print("Copying " + image + " to " + bin_dir)
        shutil.copy(image, bin_dir)
    
def main():
    parser = argparse.ArgumentParser(description='Kernel size history tool-box.')
    parser.add_argument('-f', '--fetch-sources', dest='get', action='store_const',
                        const=True, default=False,
                        help='fetch source archives')
    parser.add_argument('-x', '--extract-sources', dest='extract', action='store_const',
                        const=True, default=False,
                        help='extract sources (all sources must have been fetched)')
    parser.add_argument('-b', '--build-images', dest='build', action='store_const',
                        const=True, default=False,
                        help='build images (all sources must have been extracted)')
    parser.add_argument('-d', '--delete-sources', dest='delete_sources', action='store_const',
                        const=True, default=False,
                        help='delete the sources when done')
    parser.add_argument('-a', '--all', dest='all', action='store_const',
                        const=True, default=False,
                        help='perform all steps')
    parser.add_argument('versions', nargs='*', type=str,
                        default=defaults.versions,
                        help='kernel version(s) to perform specified operations on (default: %(default)s)')
    parser.add_argument('--download-dir', dest='dl_dir',
                        type=str, default=defaults.dir.download,
                        help='download destination directory (default: %(default)s)')
    parser.add_argument('--build-dir', dest='build_dir',
                        type=str, default=defaults.dir.build,
                        help='build directory (default: %(default)s)')
    parser.add_argument('--bin-dir', dest='bin_dir',
                        type=str, default=defaults.dir.bin,
                        help='destination directory for built images (default: %(default)s)')
    parser.add_argument('--source-mirror', dest='src_mirror',
                        type=str, default=defaults.sourceMirror,
                        help='download destination directory (default: %(default)s)')
    parser.add_argument('--make-args', dest='make_args',
                        type=str, default="-j",
                        help='make arguments (default: %(default)s)')
    parser.add_argument('--arch', dest='arch',
                        type=str, default="x86",
                        help='architecture (default: %(default)s)')
    parser.add_argument('--kernel-defconfig', dest='kernel_defconfig',
                        type=str, default="allnoconfig",
                        help='kernel defconfig to configure with (default: %(default)s)')
    
    args = parser.parse_args()
    
    for version in args.versions:
        if args.all or args.get:
            fetchKernelSource(args, version)
        if args.all or args.extract:
            extractKernelSource(args, version)
        if args.all or args.build:
            buildKernelImages(args, version)
        if args.all or args.delete_sources:
            deleteKernelSource(args, version)

if __name__ == "__main__":
    main()
