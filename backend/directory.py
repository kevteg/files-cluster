import fileinput
import os

def getFilesObjects(directory, files = None, binary = True):
    all_files = []
    files_name = None
    if files:
         files_name = [l[0] for l in files]
    # print("needed_files: ")
    # print(files_name)
    files = getFilesAtDirectory(directory, files_name, add_path = True, size = False)
    # print(files)
    try:
        for file_name in files:
            all_files.append(open(file_name, "rb" if binary else "r"))
    except Exception as e:
        print(e)

    return all_files

def getFilesAtDirectory(directory, needed_files = None, add_path = False, size = True):
    #retorna none si no existe el directorio y [] si está vacio
    try:
        results = []
        for (dirpath, dirnames, filenames) in os.walk(directory):
            if needed_files:
                if size:
                    results.extend(((((dirpath + '/') if add_path else '') + nfile) if nfile in needed_files else '', os.path.getsize((dirpath + '/') + nfile) if nfile in needed_files else '') for nfile, nfile in zip(filenames, filenames))
                else:
                    results.extend((((dirpath + '/') if add_path else '') + nfile)  if nfile in needed_files else '' for nfile in filenames)
            else:
                if size:
                    results.extend(((((dirpath + '/') if add_path else '') + nfile), os.path.getsize((dirpath + '/') + nfile)) for nfile, nfile in zip(filenames, filenames))
                else:
                    results.extend((((dirpath + '/') if add_path else '') + nfile) for nfile in filenames)
            break
        else:
            results = None
    except Exception as e:
        print(e)
        results = []
    return results
