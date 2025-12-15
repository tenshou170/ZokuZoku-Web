import type { ITreeNode, IStoryTextSlot, IEntryTreeNode } from "./sharedTypes";
import { StoryTextSlotType } from "./sharedTypes";

// Copied/adapted from storyEditor.ts

export enum DifferenceFlag {
    None = 0,
    GenderMale = 2,
    GenderFemale = 4
}

export interface StoryBlockData {
    name: string;
    text: string;
    nextBlock: number;
    differenceFlag: number;
    cueId: number;
    choices: StoryChoiceData[];
    colorTexts: StoryColorTextData[];
}

export interface StoryChoiceData {
    text: string;
    nextBlock: number;
    differenceFlag: number;
}

export interface StoryColorTextData {
    text: string;
}

export interface ExtractedStoryData {
    title: string;
    blockList: StoryBlockData[];
}

export function formatStoryData(timelineData: ExtractedStoryData) {
    const nodes: ITreeNode<IStoryTextSlot>[] = [];
    let resTitle: string | undefined;

    // Title Node
    if (timelineData.title && timelineData.title !== "0") {
        nodes.push({
            type: "entry",
            id: "title",
            name: "Title",
            icon: "whole-word",
            content: [{ content: timelineData.title }],
            next: 0
        });
        resTitle = timelineData.title;
    }

    let prevMaleNode: IEntryTreeNode | undefined;
    let prevFemaleNode: IEntryTreeNode | undefined;

    const voiceCues: [string, number][] = [];
    let globalCueOffset = 0;

    // Block Processing
    for (const [i, block] of timelineData.blockList.entries()) {
        const content: IStoryTextSlot[] = [
            {
                content: block.name,
                userData: { type: StoryTextSlotType.Name },
                tooltip: "Name"
            },
            {
                content: block.text,
                multiline: true,
                userData: { type: StoryTextSlotType.Content },
                tooltip: "Content"
            }
        ];

        // Choices
        for (const choiceData of block.choices) {
            let tooltip: string | undefined;
            let gender: "male" | "female" | undefined;
            switch (choiceData.differenceFlag) {
                case DifferenceFlag.GenderMale:
                    tooltip = "Male trainer choice";
                    gender = "male";
                    break;
                case DifferenceFlag.GenderFemale:
                    tooltip = "Female trainer choice";
                    gender = "female";
                    break;
                default:
                    tooltip = "Choice";
                    break;
            }
            content.push({
                content: choiceData.text,
                userData: { type: StoryTextSlotType.Choice, gender },
                link: choiceData.nextBlock - 1, // Adjust for 0-based index? Verify logic.
                // Assuming nextBlock is 1-based from the game/UnityPy
                tooltip
            });
        }

        // Color Texts
        for (const colorTextInfo of block.colorTexts) {
            content.push({
                content: colorTextInfo.text,
                userData: { type: StoryTextSlotType.ColorText },
                tooltip: "Color text"
            });
        }

        const id = i;
        let name = id.toString();
        const differenceFlag = block.differenceFlag;

        function updatePrevMaleNode() {
            if (prevMaleNode && id >= +prevMaleNode.next!) {
                prevMaleNode.next = id;
                prevMaleNode = undefined;
            }
        }

        function updatePrevFemaleNode() {
            if (prevFemaleNode && id >= +prevFemaleNode.next!) {
                prevFemaleNode.next = id;
                for (const slot of prevFemaleNode.content) {
                    if (slot.link) { slot.link = id; }
                }
                prevFemaleNode = undefined;
            }
        }

        // Voice Cue Logic
        let cueOffset = 0;
        switch (differenceFlag) {
            case DifferenceFlag.GenderMale:
                name += " (male trainer)";
                updatePrevMaleNode();
                cueOffset = 1;
                break;
            case DifferenceFlag.GenderFemale:
                name += " (female trainer)";
                updatePrevFemaleNode();
                break;
            default:
                updatePrevMaleNode();
                updatePrevFemaleNode();
                break;
        }

        const node: ITreeNode<IStoryTextSlot> = {
            type: "entry",
            id,
            name,
            content,
            prev: nodes[nodes.length - 1]?.id,
            next: block.nextBlock - 1
        };
        nodes.push(node);

        const cueId = block.cueId;
        if (cueId !== -1) {
            voiceCues.push([id.toString(), cueId + cueOffset + globalCueOffset]);
        }

        switch (differenceFlag) {
            case DifferenceFlag.GenderMale:
                prevMaleNode = node;
                break;
            case DifferenceFlag.GenderFemale:
                prevFemaleNode = node;
                if (cueId !== -1) {
                    globalCueOffset += 1;
                }
                break;
        }
    }

    return {
        title: resTitle,
        nodes,
        voiceCues
    };
}
