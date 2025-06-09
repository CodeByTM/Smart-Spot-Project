The "SmartSpot" project, addresses the common and often frustrating problem of finding reliable parking in busy areas by offering a paid membership parking lot solution.
This system ensures that members have guaranteed parking availability, significantly reducing the time and stress associated with searching for parking. 
Utilizing a Raspberry Pi microcontroller and Python 3.7, SmartSpot integrates various sensors and output devices to create an efficient and user-friendly experience.
Members access this parking lot through secure fobs, allowing only members to enter. Upon arrival, a user interacts with the system through a keypad with options for those with a fob, those who forgot their fob, and non-members.
Members with a fob can simply tap it to gain entry, with the LED turning green, the LCD displaying a welcome message and the number of available spots , and the speaker playing an audio message with instructions.
The gate opened momentarily. If a member forgets their fob, they can enter their secure passphrase on the keypad, and if it matches the database, the operator can open the gate remotely via the HTTP webpage. 
Non-members are instructed to contact the admin for details.
Sensors constantly monitor the parking spots, updating the system on the number of available spaces out of the six total spots. 
LED indicators provide clear, immediate visual feedback. Additionally, a web camera feeds into the HTTP website for security purposes, allowing security professionals to monitor the entire premises in real-time.
To exit the parking garage, users press a push button to open the gate. A proximity sensor ensures the car has cleared the area before closing the gate, preventing accidents, and ensuring smooth operation. 
Overall, SmartSpot's innovative approach to parking management offers a dependable solution for members, maximizing the utility of parking facilities and providing peace of mind with enhanced security measures and real-time monitoring throughout the entire parking lot.
