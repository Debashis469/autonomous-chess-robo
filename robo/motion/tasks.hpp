#ifndef TASKS_HPP
#define TASKS_HPP

bool pick(double x, double y, double z);
bool place(double x, double y, double z);

bool pickAndPlace(
    double sx, double sy, double sz,
    double dx, double dy, double dz
);

bool pickAndThrow(
    double sx, double sy, double sz,
    double tx, double ty, double tz
);

bool moveRest(double x, double y, double z);

#endif
