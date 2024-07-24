from armchecker import ArmChecker

def main():
    arm_checker = ArmChecker('/dev/ttyACM0')
    arm_checker.run()

if __name__ == "__main__":
    main()