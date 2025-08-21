export interface WeekAdherenceInput {
  activeDays: boolean[]; // length 7 starting Monday
  workoutsDone: Date[];
}

export function calcWeekAdherence({ activeDays, workoutsDone }: WeekAdherenceInput) {
  const countPlanned = activeDays.filter(Boolean).length;
  const doneSet = new Set(workoutsDone.map((d) => ((d.getDay() + 6) % 7) + 1));
  let countDone = 0;
  activeDays.forEach((active, idx) => {
    if (active && doneSet.has(idx + 1)) countDone++;
  });
  const rate = countPlanned === 0 ? 0 : Math.round((countDone / countPlanned) * 100);
  return { countPlanned, countDone, rate };
}
