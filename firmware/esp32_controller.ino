#include <SCServo.h>

// ===== OBJECTS =====
SMS_STS st;
SCSCL sc;

// ===== UART =====
#define S_RXD 18
#define S_TXD 19

// ===== SPEED =====
int SERVO_SPEED = 75; // 75
int SERVO_ACC   = 1; // 1

// ===== GRIPPER =====
#define GRIPPER_ID 5
int GRIP_OPEN  = 345;
int GRIP_CLOSE = 400;
#define GRIPPER_SETTLE_MS 250

// ===== TRAJECTORY SETTINGS =====
#define MAX_WAYPOINTS    200
#define MAX_PACKET_CHARS 4096
#define POS_TOLERANCE    60
#define ARM_TIMEOUT_MS   120000

// -------- CALIBRATION --------
float m1_ang[] = {-90, -45, 0, 45, 90};
int   m1_pos[] = {1166, 1648, 2107, 2550, 3045};

float m2_ang[] = {11, 45, 90, 135, 180};
int   m2_pos[] = {1811, 1473, 987, 507, 42};

float m3_ang[] = {-168, -135, -90, -45};
int   m3_pos[] = {2951, 2527, 2015, 1488};

float m4_ang[] = {-90, -45, 0, 45, 90};
int   m4_pos[] = {3580, 3030, 2561, 1985, 1544};

// -------- STRUCT --------
struct Waypoint {
  float a1, a2, a3, a4;
  char grip;
};

Waypoint traj[MAX_WAYPOINTS];
int trajCount = 0;

// -------- SERIAL --------
String packetBuffer;
bool collectingPacket = false;

// Global parse buffer to avoid large stack allocation
char parseBuf[MAX_PACKET_CHARS];

// -------- INTERPOLATION --------
int interpolate(float angle, float *ang, int *pos, int size)
{
  if (angle <= ang[0]) return pos[0];
  if (angle >= ang[size - 1]) return pos[size - 1];

  for (int i = 0; i < size - 1; i++)
  {
    if (angle >= ang[i] && angle <= ang[i + 1])
    {
      float t = (angle - ang[i]) / (ang[i + 1] - ang[i]);
      return pos[i] + t * (pos[i + 1] - pos[i]);
    }
  }

  return pos[0];
}

// -------- FEEDBACK CHECK --------
bool armReached(int t1, int t2, int t3, int t4)
{
  int c1 = st.ReadPos(1);
  int c2 = st.ReadPos(2);
  int c3 = st.ReadPos(3);
  int c4 = st.ReadPos(4);

  int e1 = abs(c1 - t1);
  int e2 = abs(c2 - t2);
  int e3 = abs(c3 - t3);
  int e4 = abs(c4 - t4);

  // Throttled debug print
  static unsigned long lastDbg = 0;
  if (millis() - lastDbg > 200)
  {
    Serial.print("Err: ");
    Serial.print(e1); Serial.print(" ");
    Serial.print(e2); Serial.print(" ");
    Serial.print(e3); Serial.print(" ");
    Serial.println(e4);
    lastDbg = millis();
  }

  return (e1 < POS_TOLERANCE &&
          e2 < POS_TOLERANCE &&
          e3 < POS_TOLERANCE &&
          e4 < POS_TOLERANCE);
}

// -------- WAIT --------
bool waitForArmToReach(int t1, int t2, int t3, int t4)
{
  unsigned long start = millis();

  while (millis() - start < ARM_TIMEOUT_MS)
  {
    if (armReached(t1, t2, t3, t4))
    {
      delay(50);
      return true;
    }

    delay(20);
  }

  return false;
}

// -------- MOVE --------
bool moveOneWaypoint(const Waypoint &wp)
{
  int t1 = interpolate(wp.a1, m1_ang, m1_pos, 5);
  int t2 = interpolate(wp.a2, m2_ang, m2_pos, 5);
  int t3 = interpolate(wp.a3, m3_ang, m3_pos, 4);
  int t4 = interpolate(wp.a4, (m4_ang), m4_pos, 5); // 1 degree less 

  st.RegWritePosEx(1, t1, SERVO_SPEED, SERVO_ACC);
  st.RegWritePosEx(2, t2, SERVO_SPEED, SERVO_ACC);
  st.RegWritePosEx(3, t3, SERVO_SPEED, SERVO_ACC);
  st.RegWritePosEx(4, t4, SERVO_SPEED, SERVO_ACC);

  // Trigger all queued motions simultaneously
  st.RegWriteAction();

  if (!waitForArmToReach(t1, t2, t3, t4))
  {
    Serial.println("ERR: arm timeout");
    return false;
  }

  int gripTarget = (wp.grip == 'o') ? GRIP_OPEN : GRIP_CLOSE;
  sc.WritePosEx(GRIPPER_ID, gripTarget, 200, 10);

  // Give gripper time to actually open/close before next waypoint
  delay(GRIPPER_SETTLE_MS);

  return true;
}

// -------- PARSER --------
bool parseTrajectory(const String &input)
{
  int n = input.length();

  if (n < 2) return false;
  if (input[0] != '[' || input[n - 1] != ']') return false;

  if (n >= MAX_PACKET_CHARS)
  {
    Serial.println("ERR: packet too long");
    return false;
  }

  // Copy into global buffer, not stack
  for (int i = 0; i < n; i++)
  {
    char c = input[i];
    parseBuf[i] = (c == '[' || c == ']' || c == ',') ? ' ' : c;
  }
  parseBuf[n] = '\0';

  trajCount = 0;
  int idx = 0;
  Waypoint current = {0, 0, 0, 0, 'o'};

  char *token = strtok(parseBuf, " \t\r\n");

  while (token != NULL)
  {
    int slot = idx % 5;

    if (slot == 0) current.a1 = atof(token);
    else if (slot == 1) current.a2 = atof(token);
    else if (slot == 2) current.a3 = atof(token);
    else if (slot == 3) current.a4 = atof(token);
    else if (slot == 4)
    {
      if (trajCount >= MAX_WAYPOINTS)
      {
        Serial.println("ERR: too many waypoints");
        return false;
      }

      current.grip = token[0];

      if (current.grip != 'o' && current.grip != 'c')
      {
        Serial.println("ERR: invalid gripper token");
        return false;
      }

      traj[trajCount++] = current;
    }

    idx++;
    token = strtok(NULL, " \t\r\n");
  }

  return (trajCount > 0 && idx % 5 == 0);
}

// -------- EXECUTION --------
bool executeTrajectory()
{
  Serial.print("Executing ");
  Serial.print(trajCount);
  Serial.println(" waypoints...");

  for (int i = 0; i < trajCount; i++)
  {
    Serial.print("Waypoint ");
    Serial.print(i + 1);
    Serial.print("/");
    Serial.println(trajCount);

    if (!moveOneWaypoint(traj[i]))
    {
      Serial.println("Stopped.");
      Serial.println("0");   // fail ACK
      return false;
    }
  }

  Serial.println("Done.");
  Serial.println("1");       // success ACK
  return true;
}

// -------- SETUP --------
void setup()
{
  Serial.begin(115200);
  Serial1.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);

  st.pSerial = &Serial1;
  sc.pSerial = &Serial1;

  packetBuffer.reserve(MAX_PACKET_CHARS);

  delay(1000);

  for (int i = 1; i <= 4; i++)
    st.EnableTorque(i, 1);

  sc.EnableTorque(GRIPPER_ID, 1);

  Serial.println("Ready.");
}

// -------- LOOP --------
void loop()
{
  while (Serial.available())
  {
    char c = Serial.read();

    if (c == '[')
    {
      collectingPacket = true;
      packetBuffer = "[";
      continue;
    }

    if (!collectingPacket)
      continue;

    if (packetBuffer.length() >= MAX_PACKET_CHARS - 1)
    {
      Serial.println("ERR: packet overflow");
      Serial.println("0");
      collectingPacket = false;
      packetBuffer = "";
      continue;
    }

    packetBuffer += c;

    if (c == ']')
    {
      collectingPacket = false;

      if (!parseTrajectory(packetBuffer))
      {
        Serial.println("Invalid format");
        Serial.println("0");
      }
      else
      {
        executeTrajectory();
      }

      packetBuffer = "";
    }
  }
}