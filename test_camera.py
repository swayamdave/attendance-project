import cv2
import sys

def test_camera():
    print("OpenCV version:", cv2.__version__)
    print("Python version:", sys.version)
    
    try:
        print("Initializing camera...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not open camera")
            return False
            
        print("Camera opened successfully")
        
        # Read a test frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            return False
            
        print("Successfully read frame from camera")
        
        # Display test frame
        cv2.imshow('Camera Test', frame)
        print("Press any key to exit...")
        cv2.waitKey(0)
        
        return True
        
    except Exception as e:
        print(f"Error during camera test: {str(e)}")
        return False
    finally:
        if 'cap' in locals():
            cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    if test_camera():
        print("Camera test successful!")
    else:
        print("Camera test failed!") 