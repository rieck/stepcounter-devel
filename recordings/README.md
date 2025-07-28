# Step Counter Recordings

This directory contains recorded sensor data from step counter experiments. The data is organized by sensor configuration and activity type for analysis and algorithm development.

## Directory Structure

The recordings are organized into subdirectories based on sensor configuration:

- **`l1-12hz/`** - L1 magnitude of sensor at 12Hz sampling rate
- **`l2-12hz/`** - L2 magnitude of sensor at 12Hz sampling rate  
- **`l2-25hz/`** - L2 magnitude of sensor at 25Hz sampling rate

## File Naming Convention

Each recording file follows the pattern: `{activity}-{footwear}.b64`

### Activity Types

- **`fast-walking`** - Fast walking motion (higher intensity steps)
- **`normal-walking`** - Normal walking pace (typical daily walking)
- **`slow-walking`** - Slow walking motion (lower intensity steps)
- **`pc-working`** - Desk work activities (sitting and typing)

### Footwear Types

- **`bf`** - Bare feet 😂
- **`sh`** - Shoes

## Data Format

All recordings are stored in base64 encoded format (`.b64` extension) as returned from SensorWatch. The raw data contains accelerometer readings and metadata from the `stepcounter_logging_face`.

## Data Retrieval

The data is retrieved directly from the serial interface of SensorWatch using the following commands.

### Data Capture

```bash
cat /dev/cu.usbmodem224201 | tee recorded-data.b64
```

Records anything output by SensorWatch including a few console logs but also the recorded data stream.

### Data Encoding

```bash
echo "b64encode log.scl" > /dev/cu.usbmodem224201
```

Encodes the raw log file to base64 format for storage.

### Data Cleanup

```bash
echo "rm log.scl" > /dev/cu.usbmodem224201
```

Removes temporary log files from the sensor device.

## Research Applications

This dataset enables research on:

- **Step Detection Accuracy**: Compare L1 vs L2 magnitude effectiveness
- **Sampling Rate Impact**: Analyze 12Hz vs 25Hz performance
- **Footwear Effects**: Study bare feet vs shoes on detection
- **Activity Classification**: Generalization across activity types
- **Algorithm Optimization**: Develop robust step counting algorithms
