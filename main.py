import asyncio, os
from ocr.capture import capture_screen
from ocr.process import process_image
from spotify.auth import authenticate
from spotify.api import search_song, check_song_in_queue, add_song_to_queue
from gui.overlay import create_tkinter_window, calculate_bounding_box
from vrc.vrc_osc_notifier import OSCNotifier


async def main():
    # Authenticate user for Spotify API and initialize OSCNotifier
    sp = await authenticate()
    vrc_notifier = OSCNotifier()

    # Calculate the bounding box parameters and create the overlay window
    sleft, stop, box_width, box_height = calculate_bounding_box(0.3, height_scale=0.5, width_scale=0.7)
    root = create_tkinter_window(sleft, stop, box_width, box_height, 3)

    # Variables to keep track of the current song
    prev_song_name = None
    prev_spotify_song_info = None

    try:
        while True:
            # Capture screenshot and process it with OCR to extract song name
            screenshot = capture_screen(sleft, stop, box_width, box_height)
            song_name = process_image(screenshot)

            # If a new song is detected, search for it on Spotify and add to queue if not already there
            if song_name and (song_name != prev_song_name):
                print(f"Song name detected: {song_name}")
                song_id, spotify_song_info = await search_song(sp, song_name)

                if song_id and not await check_song_in_queue(sp, song_id):
                    print(f"Adding {spotify_song_info} to queue...")
                    await add_song_to_queue(sp, song_id)
                    print(f"{spotify_song_info} added to queue!")
                    vrc_notifier.notify_song_added(spotify_song_info)
                else:
                    print(f"{spotify_song_info} is already in queue!")
                    vrc_notifier.notify_song_already_in_queue(spotify_song_info)

                # Update current song
                prev_song_name, prev_spotify_song_info = song_name, spotify_song_info

            # Update the Tkinter window
            root.update()

            message_filename = 'message.txt'
            if os.path.exists(message_filename):
                with open(message_filename, 'r') as f:
                    custom_message = f.read().strip()
                
                # # Clear the message file after reading it
                # with open(message_filename, 'w') as f:
                #     pass
            else:
                custom_message = ""

            # Update the chat in VRChat and sleep for 2.5 seconds
            if custom_message:
                vrc_notifier.send_custom_message(custom_message)
            else:
                vrc_notifier.send_custom_message(f"Please help me test this. Type @@ <song name> in front of me. Last Added: {prev_spotify_song_info}")
            
            await asyncio.sleep(2.5)

    except KeyboardInterrupt:
        print("Program interrupted.")
        vrc_notifier.send_custom_message("I killed the program with my bare hands, be back in a sec")
        
    finally:
        root.destroy()

if __name__ == "__main__":
    asyncio.run(main())
