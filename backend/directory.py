import fileinput
import os

def getFilesObjects(directory, files = None, binary = True):
    all_files = []
    files = getFilesAtDirectory(directory) if files is None else files
    try:
        for file_name in files:
            all_files.append(open(file_name, "rb" if binary else "r"))
        else:
            print("Empty directory")
    except:
        pass

    return all_files

def getFilesAtDirectory(directory):
    #retorna none si no existe el directorio y [] si está vacio
    try:
        results = []
        for (dirpath, dirnames, filenames) in os.walk(directory):
            results.extend(dirpath + '/' + nfile for nfile in filenames)
            break
        else:
            results = None
    except:
        results = []
    return results
