import cv2

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        print(f"Cursor position: ({x}, {y})")

def main():
    # Load the image
    image = cv2.imread("c:\\Primary_Flight_Display_of_a_Boeing_737-800.png")

    # Create a window to display the image
    cv2.namedWindow("Image")

    # Set the mouse callback function
    cv2.setMouseCallback("Image", mouse_callback)

    while True:
        # Display the image
        cv2.imshow("Image", image)

        # Check for key press
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    # Clean up
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()