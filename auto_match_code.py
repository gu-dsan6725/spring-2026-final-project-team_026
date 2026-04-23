import os
import shutil

def find_and_cp():
    ls = os.listdir("old-demos/demo")
    ls_cp = []
    for target_file in ls:
        found = False

        for root, dirs, files in os.walk("cpython-2.0"):
            for file in files:
                if file.endswith(".py") and file == target_file:
                    src = os.path.join(root, file)
                    dst = os.path.join("test_set/x", file)
                    dst_y = os.path.join("test_set/y", file)
                    ls_cp.append(dst)
                    shutil.copy(src, dst)
                    old_demo_src = os.path.join("old-demos/demo", target_file)
                    shutil.copy(old_demo_src , dst_y)
                    found = True

                    break

            if found:
                break
    return ls_cp

def find_and_cp_2():
    ls = os.listdir("old-demos/scripts")
    ls_cp = []
    count = 0
    for target_file in ls:
        found = False
        if count >= 12:
                break
        for root, dirs, files in os.walk("cpython-2.0"):
            if count >= 12:
                break
            for file in files:
                if file.endswith(".py") and file == target_file:
                    src = os.path.join(root, file)
                    dst = os.path.join("test_set/x", file)
                    dst_y = os.path.join("test_set/y", file)
                    ls_cp.append(dst)
                    shutil.copy(src, dst)
                    old_demo_src = os.path.join("old-demos/scripts", target_file)
                    shutil.copy(old_demo_src , dst_y)
                    found = True
                    count +=1

                    break

            if found:
                break
    return ls_cp

def main():
    print(find_and_cp())
    print(find_and_cp_2())

if __name__ == '__main__':
    main()
